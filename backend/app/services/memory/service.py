from __future__ import annotations

import os
import re
import threading
import logging
import csv
from dataclasses import dataclass, field
from collections.abc import Iterator
from datetime import datetime, timezone
from io import StringIO

from app.core.config import MemoryConfig, config
from mem0 import Memory
from openai import OpenAIError


DEFAULT_USER_ID = "default-user"

VOICE_ASSISTANT_SYSTEM_PROMPT = """You generate final text for VieNeu-TTS.
Return only plain speakable text for tts.infer(text=...).
Use plain spoken text only.
Write mainly in natural Vietnamese unless the user asks otherwise. Sound like a real human assistant. Keep replies warm, conversational, concise, and easy to say aloud. Use complete sentences, short sentence length, and punctuation for natural pauses.
Do not use Markdown, bullets, tables, headings, code blocks, links, citations, emojis, labels, stage directions, or explanations about TTS.
Make all text voice-friendly. Convert numbers, dates, times, currencies, symbols, measurements, and abbreviations into spoken form. Spell English abbreviations when needed, for example API as A P I. Keep English technical terms only when they sound more natural than translating them.
If the user asks for lists, code, links, tables, or dense technical details, summarize them in smooth spoken prose and mention that details can be shown on screen.
You may use VieNeu-TTS emotion tags only when clearly helpful: [cười], [thở dài], [hắng giọng]. Do not use them in normal replies.
Final output must contain only the text to be spoken.
"""


@dataclass(frozen=True)
class MemoryReply:
    text: str
    user_id: str


@dataclass(frozen=True)
class MemorySearchResult:
    memory: str
    score: float | None
    id: str | None = None
    user_id: str | None = None
    categories: list[str] = field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None
    agent_id: str | None = None
    run_id: str | None = None
    actor_id: str | None = None
    role: str | None = None
    metadata: dict[str, object] | None = None
    extra_fields: dict[str, object] = field(default_factory=dict)

    @classmethod
    def from_mem0(cls, item: dict[str, object]) -> MemorySearchResult:
        memory_text = item.get("memory")
        if not isinstance(memory_text, str):
            raise ValueError("Mem0 search result is missing memory text.")

        known_keys = {
            "id",
            "memory",
            "score",
            "user_id",
            "categories",
            "created_at",
            "updated_at",
            "agent_id",
            "run_id",
            "actor_id",
            "role",
            "metadata",
        }
        score = item.get("score")
        raw_categories = item.get("categories")
        categories = raw_categories if isinstance(raw_categories, list) else []
        metadata = item.get("metadata")

        return cls(
            id=str(item["id"]) if item.get("id") is not None else None,
            memory=memory_text,
            score=float(score) if isinstance(score, (int, float)) else None,
            user_id=str(item["user_id"]) if item.get("user_id") is not None else None,
            categories=[str(category) for category in categories],
            created_at=str(item["created_at"])
            if item.get("created_at") is not None
            else None,
            updated_at=str(item["updated_at"])
            if item.get("updated_at") is not None
            else None,
            agent_id=str(item["agent_id"]) if item.get("agent_id") is not None else None,
            run_id=str(item["run_id"]) if item.get("run_id") is not None else None,
            actor_id=str(item["actor_id"]) if item.get("actor_id") is not None else None,
            role=str(item["role"]) if item.get("role") is not None else None,
            metadata=metadata if isinstance(metadata, dict) else None,
            extra_fields={key: value for key, value in item.items() if key not in known_keys},
        )

    def as_telemetry(self) -> dict[str, object]:
        telemetry = dict(self.extra_fields)
        for key in (
            "id",
            "user_id",
            "categories",
            "created_at",
            "updated_at",
            "agent_id",
            "run_id",
            "actor_id",
            "role",
            "metadata",
        ):
            value = getattr(self, key)
            if value:
                telemetry[key] = value
        telemetry["memory"] = self.memory
        telemetry["score"] = self.score
        return telemetry


@dataclass(frozen=True)
class MemoryPersistResult:
    actions: list[dict[str, object]]
    action_counts: dict[str, int]
    raw_result: dict[str, object] | None


class MemoryServiceError(Exception):
    pass


class _StructuredMemoryActionHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.actions: list[dict[str, object]] = []

    def emit(self, record: logging.LogRecord) -> None:
        if isinstance(record.msg, dict) and isinstance(record.msg.get("event"), str):
            self.actions.append(dict(record.msg))


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
            self.build_response_messages(query, memories),
            extra_body=self.memory_config.to_deepseek_extra_body(),
        )

        response_text = str(response).strip()
        response_text = self._clean_response_for_speech(response_text)
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

    def build_response_messages(
        self,
        query: str,
        memories: list[MemorySearchResult],
    ) -> list[dict[str, str]]:
        local_now = datetime.now().astimezone().isoformat()
        utc_now = datetime.now(timezone.utc).isoformat()
        memory_context = self._format_memory_context_csv(memories)
        if not memory_context:
            memory_context = "No relevant memories yet."

        return [
            {
                "role": "system",
                "content": VOICE_ASSISTANT_SYSTEM_PROMPT,
            },
            {
                "role": "system",
                "content": (
                    f"Current local time: {local_now}\n"
                    f"Current UTC time: {utc_now}\n"
                    "Use timestamps to interpret relative time phrases.\n\n"
                    f"Relevant memories CSV:\n{memory_context}"
                ),
            },
            {
                "role": "user",
                "content": query,
            },
        ]

    def stream_response(
        self,
        query: str,
        memories: list[MemorySearchResult],
        messages: list[dict[str, str]] | None = None,
    ) -> Iterator[str]:
        memory = self.load_memory()
        response_messages = messages or self.build_response_messages(query, memories)
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
        action_handler = _StructuredMemoryActionHandler()
        mem0_logger = logging.getLogger("mem0.memory.main")
        previous_level = mem0_logger.level
        mem0_logger.setLevel(logging.INFO)
        mem0_logger.addHandler(action_handler)
        try:
            raw_result = memory.add(
                [
                    {"role": "user", "content": query},
                    {"role": "assistant", "content": response_text},
                ],
                user_id=user_id,
            )
        finally:
            mem0_logger.removeHandler(action_handler)
            mem0_logger.setLevel(previous_level)

        actions = self._memory_actions(raw_result, action_handler.actions)
        return MemoryPersistResult(
            actions=actions,
            action_counts=self._memory_action_counts(actions),
            raw_result=raw_result if isinstance(raw_result, dict) else None,
        )

    def _memory_actions(
        self,
        raw_result: object,
        logged_actions: list[dict[str, object]],
    ) -> list[dict[str, object]]:
        actions: list[dict[str, object]] = []
        returned_results = raw_result.get("results", []) if isinstance(raw_result, dict) else []

        if isinstance(returned_results, list):
            for item in returned_results:
                if isinstance(item, dict) and isinstance(item.get("event"), str):
                    actions.append(self._normalize_memory_action(item))

        for item in logged_actions:
            event = item.get("event")
            if not isinstance(event, str):
                continue
            normalized = self._normalize_memory_action(item)
            has_matching_action = any(
                action.get("event") == normalized.get("event")
                and action.get("memory") == normalized.get("memory")
                for action in actions
            )
            if event == "NONE" or not has_matching_action:
                actions.append(normalized)

        return actions

    def _normalize_memory_action(self, action: dict[str, object]) -> dict[str, object]:
        memory_text = action.get("memory") or action.get("text") or ""
        previous_memory = action.get("previous_memory") or action.get("old_memory")
        normalized: dict[str, object] = {
            "id": str(action.get("id", "")),
            "event": str(action["event"]),
            "memory": str(memory_text),
        }
        if previous_memory:
            normalized["previous_memory"] = str(previous_memory)
        return normalized

    def _memory_action_counts(
        self,
        actions: list[dict[str, object]],
    ) -> dict[str, int]:
        counts: dict[str, int] = {}
        for action in actions:
            event = str(action.get("event", "UNKNOWN"))
            counts[event] = counts.get(event, 0) + 1
        return counts

    def _format_memory_context_csv(
        self,
        memories: list[MemorySearchResult],
    ) -> str:
        if not memories:
            return ""

        output = StringIO()
        fieldnames = [
            "memory",
            "created_at",
            "updated_at",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for item in memories:
            writer.writerow(
                {
                    "memory": item.memory,
                    "created_at": item.created_at or "",
                    "updated_at": item.updated_at or "",
                }
            )
        return output.getvalue().strip()

    def _clean_response_for_speech(self, text: str) -> str:
        spoken_text = text.strip()
        spoken_text = re.sub(r"```[^\n`]*\n?", "", spoken_text)
        spoken_text = spoken_text.replace("```", "")
        spoken_text = re.sub(r"\[([^\]]+)]\([^)]+\)", r"\1", spoken_text)
        spoken_text = re.sub(r"`([^`]+)`", r"\1", spoken_text)
        spoken_text = re.sub(r"(?m)^\s{0,3}#{1,6}\s+", "", spoken_text)
        spoken_text = re.sub(r"(?m)^\s*>\s?", "", spoken_text)
        spoken_text = re.sub(r"(?m)^\s*[-*+]\s+", "", spoken_text)
        spoken_text = re.sub(r"(?m)^\s*\d+[.)]\s+", "", spoken_text)
        spoken_text = re.sub(r"(?m)^\s*-{3,}\s*$", "", spoken_text)
        spoken_text = re.sub(r"([*_~]{1,3})(\S.*?\S|\S)\1", r"\2", spoken_text)
        spoken_text = re.sub(r"[*_~]{2,}", "", spoken_text)
        spoken_text = re.sub(r"[ \t]+", " ", spoken_text)
        spoken_text = re.sub(r"\s*\n+\s*", " ", spoken_text)
        spoken_text = re.sub(r"\s{2,}", " ", spoken_text)
        return spoken_text.strip()


memory_service = MemoryService()
