from __future__ import annotations

import json
import os
import threading
from collections.abc import Iterator
from datetime import datetime, timezone

from app.core.config import MemoryConfig, config
from app.services.auth import AuthService, auth_service
from app.services.memory.categories import (
    MemoryCategoryKey,
    parse_memory_category,
)
from app.services.memory.conversation_history import (
    ConversationHistory,
    conversation_history,
)
from app.services.memory.persistence import (
    MEMORY_PLANNER_TOOL,
    MemoryAction,
    memory_action_counts,
)
from app.services.memory.prompt import (
    build_memory_planner_messages,
    build_response_messages,
)
from app.services.memory.speech import clean_response_for_speech
from app.services.memory.types import (
    ManagedMemoryItem,
    MemoryPersistResult,
    MemoryReply,
    MemorySearchResult,
    MemoryNotFoundError,
    MemoryServiceError,
)
from mem0 import Memory
from openai import OpenAIError


class MemoryService:
    """Lazy wrapper around Mem0 memory storage."""

    def __init__(
        self,
        memory_config: MemoryConfig = config.memory,
        history: ConversationHistory = conversation_history,
        auth: AuthService = auth_service,
    ) -> None:
        self.memory_config = memory_config
        self.history = history
        self.auth = auth
        self._memory: Memory | None = None
        self._lock = threading.RLock()

    def load_memory(self) -> Memory:
        with self._lock:
            if self._memory is None:
                self.memory_config.mem0_dir.mkdir(parents=True, exist_ok=True)
                os.environ.setdefault("MEM0_DIR", str(self.memory_config.mem0_dir))

                self._memory = Memory.from_config(self.memory_config.to_mem0_config())
            return self._memory

    def respond(self, text: str, user_id: str) -> MemoryReply:
        query = text.strip()
        if not query:
            raise MemoryServiceError("Memory service received empty text.")

        memory = self.load_memory()
        memory_enabled = self.is_enabled(user_id)
        memories = self.search_memory_results(query, user_id) if memory_enabled else []
        recent_messages = self.history.messages_for(user_id)
        response = memory.llm.generate_response(
            build_response_messages(query, memories, recent_messages),
            extra_body=self.memory_config.to_deepseek_extra_body(),
        )

        response_text = clean_response_for_speech(str(response).strip())
        if not response_text:
            raise MemoryServiceError("Memory service returned an empty response.")

        if memory_enabled:
            self.persist_conversation(
                query,
                response_text,
                user_id,
                recent_messages,
                memories,
            )
        self.history.record_turn(user_id, query, response_text)

        return MemoryReply(text=response_text, user_id=user_id)

    def is_enabled(self, user_id: str) -> bool:
        return self.auth.is_memory_enabled(user_id)

    def set_enabled(self, user_id: str, enabled: bool) -> bool:
        return self.auth.set_memory_enabled(user_id, enabled)

    def list_memories(self, user_id: str) -> list[ManagedMemoryItem]:
        memory = self.load_memory()
        result = memory.get_all(filters={"user_id": user_id}, top_k=500)
        items: list[ManagedMemoryItem] = []
        for item in result.get("results", []):
            if not isinstance(item, dict):
                continue
            try:
                memory_item = ManagedMemoryItem.from_mem0(item)
            except ValueError:
                continue
            if memory_item.user_id == user_id:
                items.append(memory_item)
        return sorted(
            items,
            key=lambda item: (
                self._parse_timestamp(item.updated_at),
                self._parse_timestamp(item.created_at),
            ),
            reverse=True,
        )

    def create_memory(
        self,
        user_id: str,
        memory_text: str,
        category: MemoryCategoryKey,
    ) -> ManagedMemoryItem:
        memory = self.load_memory()
        raw_result = memory.add(
            memory_text,
            user_id=user_id,
            metadata={"category": category},
            infer=False,
        )
        memory_id = self._added_memory_id(raw_result)
        return self.get_memory(user_id, memory_id)

    def get_memory(self, user_id: str, memory_id: str) -> ManagedMemoryItem:
        memory = self.load_memory()
        raw_item = memory.get(memory_id)
        if not isinstance(raw_item, dict):
            raise MemoryNotFoundError(f"Memory {memory_id} was not found.")

        item = ManagedMemoryItem.from_mem0(raw_item)
        if item.user_id != user_id:
            raise MemoryNotFoundError(f"Memory {memory_id} was not found.")
        return item

    def update_memory(
        self,
        user_id: str,
        memory_id: str,
        memory_text: str,
        category: MemoryCategoryKey,
    ) -> ManagedMemoryItem:
        memory = self.load_memory()
        self.get_memory(user_id, memory_id)
        memory.update(memory_id, memory_text, metadata={"category": category})
        return self.get_memory(user_id, memory_id)

    def delete_memory(self, user_id: str, memory_id: str) -> None:
        memory = self.load_memory()
        self.get_memory(user_id, memory_id)
        memory.delete(memory_id)

    def search_memory_results(
        self, query: str, user_id: str
    ) -> list[MemorySearchResult]:
        memory = self.load_memory()
        result = memory.search(
            query, filters={"user_id": user_id}, top_k=5, threshold=0.0
        )
        memories: list[MemorySearchResult] = []
        for item in result.get("results", []):
            if not isinstance(item, dict) or not isinstance(item.get("memory"), str):
                continue

            memories.append(MemorySearchResult.from_mem0(item))
        return memories

    def stream_response(
        self,
        query: str,
        memories: list[MemorySearchResult],
        messages: list[dict[str, str]] | None = None,
    ) -> Iterator[str]:
        memory = self.load_memory()
        response_messages = messages or build_response_messages(query, memories)
        try:
            stream = memory.llm.client.chat.completions.create(
                model=self.memory_config.llm_model,
                messages=response_messages,
                temperature=self.memory_config.llm_temperature,
                max_tokens=self.memory_config.llm_max_tokens,
                stream=True,
                extra_body=self.memory_config.to_deepseek_extra_body(),
            )

            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield str(delta)
        except OpenAIError as error:
            raise MemoryServiceError(str(error)) from error

    def persist_conversation(
        self,
        query: str,
        response_text: str,
        user_id: str,
        recent_messages: list[dict[str, str]] | None = None,
        candidate_memories: list[MemorySearchResult] | None = None,
    ) -> MemoryPersistResult:
        memory = self.load_memory()
        candidate_memories = candidate_memories or []
        planned_actions = self._plan_memory_actions(
            memory,
            query,
            response_text,
            recent_messages or [],
            candidate_memories,
        )
        actions = self._apply_memory_actions(memory, planned_actions, user_id)
        return MemoryPersistResult(
            actions=actions,
            action_counts=memory_action_counts(actions),
            raw_result=None,
        )

    def _plan_memory_actions(
        self,
        memory: Memory,
        query: str,
        response_text: str,
        recent_messages: list[dict[str, str]],
        candidate_memories: list[MemorySearchResult],
    ) -> list[MemoryAction]:
        try:
            response = memory.llm.generate_response(
                build_memory_planner_messages(
                    query,
                    response_text,
                    recent_messages,
                    candidate_memories,
                ),
                tools=[MEMORY_PLANNER_TOOL],
                tool_choice={
                    "type": "function",
                    "function": {"name": "plan_memory_actions"},
                },
                extra_body=self.memory_config.to_deepseek_extra_body(),
            )
        except json.JSONDecodeError:
            return []

        if not isinstance(response, dict):
            return []

        tool_calls = response.get("tool_calls")
        if not isinstance(tool_calls, list) or len(tool_calls) != 1:
            return []

        tool_call = tool_calls[0]
        if not isinstance(tool_call, dict):
            return []
        if tool_call.get("name") != "plan_memory_actions":
            return []

        arguments = tool_call.get("arguments")
        if not isinstance(arguments, dict):
            return []

        raw_actions = arguments.get("actions")
        if not isinstance(raw_actions, list) or len(raw_actions) > 3:
            return []

        candidate_by_id = {
            item.id: item.memory for item in candidate_memories if item.id is not None
        }
        actions: list[MemoryAction] = []
        for raw_action in raw_actions:
            if not isinstance(raw_action, dict):
                continue
            event = raw_action.get("event")
            if event == "NONE":
                actions.append(MemoryAction(event="NONE"))
                continue
            if event == "ADD":
                memory_text = raw_action.get("memory")
                category = parse_memory_category(raw_action.get("category"))
                if (
                    isinstance(memory_text, str)
                    and memory_text.strip()
                    and category is not None
                ):
                    actions.append(
                        MemoryAction(
                            event="ADD",
                            memory=memory_text.strip(),
                            category=category,
                        )
                    )
                continue
            if event == "UPDATE":
                memory_id = raw_action.get("id")
                memory_text = raw_action.get("memory")
                category = parse_memory_category(raw_action.get("category"))
                if (
                    isinstance(memory_id, str)
                    and memory_id in candidate_by_id
                    and isinstance(memory_text, str)
                    and memory_text.strip()
                    and category is not None
                ):
                    actions.append(
                        MemoryAction(
                            event="UPDATE",
                            id=memory_id,
                            memory=memory_text.strip(),
                            category=category,
                            previous_memory=candidate_by_id[memory_id],
                        )
                    )
                continue
            if event == "DELETE":
                memory_id = raw_action.get("id")
                if isinstance(memory_id, str) and memory_id in candidate_by_id:
                    actions.append(
                        MemoryAction(
                            event="DELETE",
                            id=memory_id,
                            previous_memory=candidate_by_id[memory_id],
                        )
                    )
        return actions

    def _apply_memory_actions(
        self,
        memory: Memory,
        planned_actions: list[MemoryAction],
        user_id: str,
    ) -> list[MemoryAction]:
        actions: list[MemoryAction] = []
        for action in planned_actions:
            if action.event == "NONE":
                actions.append(MemoryAction(event="NONE"))
                continue
            if action.event == "ADD":
                raw_result = memory.add(
                    action.memory,
                    user_id=user_id,
                    metadata={"category": action.category},
                    infer=False,
                )
                actions.extend(
                    self._memory_actions_from_add_result(
                        raw_result,
                        action.memory,
                        action.category,
                    )
                )
                continue
            if action.event == "UPDATE" and action.id:
                memory.update(
                    action.id,
                    action.memory,
                    metadata={"category": action.category},
                )
                actions.append(
                    MemoryAction(
                        event="UPDATE",
                        id=action.id,
                        memory=action.memory,
                        category=action.category,
                        previous_memory=action.previous_memory or "",
                    )
                )
                continue
            if action.event == "DELETE" and action.id:
                memory.delete(action.id)
                actions.append(
                    MemoryAction(
                        event="DELETE",
                        id=action.id,
                        memory=action.previous_memory or "",
                    )
                )
        return actions

    def _memory_actions_from_add_result(
        self,
        raw_result: object,
        memory_text: str,
        category: MemoryCategoryKey | str,
    ) -> list[MemoryAction]:
        if not isinstance(raw_result, dict):
            return [MemoryAction(event="ADD", memory=memory_text, category=category)]

        results = raw_result.get("results")
        if not isinstance(results, list) or not results:
            return [MemoryAction(event="ADD", memory=memory_text, category=category)]

        actions: list[MemoryAction] = []
        for item in results:
            if not isinstance(item, dict):
                continue
            actions.append(
                MemoryAction(
                    event="ADD",
                    id=str(item.get("id", "")),
                    memory=str(item.get("memory") or item.get("text") or memory_text),
                    category=category,
                )
            )
        return actions or [MemoryAction(event="ADD", memory=memory_text, category=category)]

    def _added_memory_id(self, raw_result: object) -> str:
        if not isinstance(raw_result, dict):
            raise MemoryServiceError("Mem0 add did not return a memory id.")
        results = raw_result.get("results")
        if not isinstance(results, list):
            raise MemoryServiceError("Mem0 add did not return results.")
        for item in results:
            if isinstance(item, dict) and item.get("id") is not None:
                return str(item["id"])
        raise MemoryServiceError("Mem0 add did not return a memory id.")

    def _parse_timestamp(self, value: str | None) -> datetime:
        if not value:
            return datetime.min.replace(tzinfo=timezone.utc)
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return datetime.min.replace(tzinfo=timezone.utc)


memory_service = MemoryService()
