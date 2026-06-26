from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Protocol

from app.services.memory import MemoryPersistResult, MemoryReply, MemorySearchResult
from app.services.tts import TtsResult


@dataclass(frozen=True)
class AssistantResult:
    audio: bytes
    media_type: str


StreamEvent = dict[str, object]
ResponseHolder = dict[str, object]


class AssistantMemory(Protocol):
    def respond(self, text: str, user_id: str) -> MemoryReply:
        ...

    def search_memory_results(
        self,
        query: str,
        user_id: str,
    ) -> list[MemorySearchResult]:
        ...

    def stream_response(
        self,
        query: str,
        memories: list[MemorySearchResult],
        messages: list[dict[str, str]],
    ) -> Iterator[str]:
        ...

    def persist_conversation(
        self,
        query: str,
        response_text: str,
        user_id: str,
        recent_messages: list[dict[str, str]] | None = None,
        candidate_memories: list[MemorySearchResult] | None = None,
    ) -> MemoryPersistResult | None:
        ...


class AssistantTts(Protocol):
    def synthesize(self, text: str, voice: object | None) -> TtsResult:
        ...
