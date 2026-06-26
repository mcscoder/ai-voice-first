from __future__ import annotations

import os
import threading
from collections.abc import Iterator

from app.core.config import MemoryConfig, config
from app.services.memory.persistence import memory_action_counts, memory_actions
from app.services.memory.prompt import (
    VOICE_ASSISTANT_SYSTEM_PROMPT,
    build_response_messages,
)
from app.services.memory.speech import clean_response_for_speech
from app.services.memory.types import (
    MemoryPersistResult,
    MemoryReply,
    MemorySearchResult,
    MemoryServiceError,
)
from mem0 import Memory
from openai import OpenAIError


DEFAULT_USER_ID = "default-user"


class MemoryService:
    """Lazy wrapper around Mem0 memory storage."""

    def __init__(self, memory_config: MemoryConfig = config.memory) -> None:
        self.memory_config = memory_config
        self._memory: Memory | None = None
        self._lock = threading.RLock()

    def load_memory(self) -> Memory:
        with self._lock:
            if self._memory is None:
                self.memory_config.mem0_dir.mkdir(parents=True, exist_ok=True)
                os.environ.setdefault("MEM0_DIR", str(self.memory_config.mem0_dir))

                self._memory = Memory.from_config(self.memory_config.to_mem0_config())
            return self._memory

    def respond(self, text: str, user_id: str = DEFAULT_USER_ID) -> MemoryReply:
        query = text.strip()
        if not query:
            raise MemoryServiceError("Memory service received empty text.")

        memory = self.load_memory()
        memories = self.search_memory_results(query, user_id)
        response = memory.llm.generate_response(
            build_response_messages(query, memories),
            extra_body=self.memory_config.to_deepseek_extra_body(),
        )

        response_text = clean_response_for_speech(str(response).strip())
        if not response_text:
            raise MemoryServiceError("Memory service returned an empty response.")

        self.persist_conversation(query, response_text, user_id)

        return MemoryReply(text=response_text, user_id=user_id)

    def search_memory_results(self, query: str, user_id: str) -> list[MemorySearchResult]:
        memory = self.load_memory()
        result = memory.search(query, user_id=user_id, limit=5)
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
    ) -> MemoryPersistResult:
        memory = self.load_memory()
        raw_result = memory.add(
            [
                {"role": "user", "content": query},
                {"role": "assistant", "content": response_text},
            ],
            user_id=user_id,
        )

        actions = memory_actions(raw_result)
        return MemoryPersistResult(
            actions=actions,
            action_counts=memory_action_counts(actions),
            raw_result=raw_result if isinstance(raw_result, dict) else None,
        )


memory_service = MemoryService()
