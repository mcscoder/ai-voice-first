from __future__ import annotations

import os
import threading
from dataclasses import dataclass

from app.core.config import MemoryConfig, config
from mem0 import Memory


DEFAULT_USER_ID = "default-user"


@dataclass(frozen=True)
class MemoryReply:
    text: str
    user_id: str


class MemoryServiceError(Exception):
    pass


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
        memories = self._search_memories(memory, query, user_id)
        response_text = self._generate_response(memory, query, memories)

        memory.add(
            [
                {"role": "user", "content": query},
                {"role": "assistant", "content": response_text},
            ],
            user_id=user_id,
        )

        return MemoryReply(text=response_text, user_id=user_id)

    def _search_memories(
        self,
        memory: Memory,
        query: str,
        user_id: str,
    ) -> list[str]:
        result = memory.search(query, user_id=user_id, limit=5)
        return [
            item["memory"]
            for item in result.get("results", [])
            if isinstance(item, dict) and isinstance(item.get("memory"), str)
        ]

    def _generate_response(
        self,
        memory: Memory,
        query: str,
        memories: list[str],
    ) -> str:
        memory_context = "\n".join(f"- {item}" for item in memories)
        if not memory_context:
            memory_context = "No relevant memories yet."

        response = memory.llm.generate_response(
            [
                {
                    "role": "system",
                    "content": (
                        "You are a helpful voice assistant. Answer naturally and "
                        "concisely. Use the provided memories when they are relevant."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Relevant memories:\n{memory_context}\n\n"
                        f"User said:\n{query}"
                    ),
                },
            ],
        )

        response_text = str(response).strip()
        if not response_text:
            raise MemoryServiceError("Memory service returned an empty response.")

        return response_text


memory_service = MemoryService()
