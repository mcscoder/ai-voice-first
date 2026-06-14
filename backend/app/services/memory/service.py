from __future__ import annotations

import os
import threading
from typing import TYPE_CHECKING, Any

from app.core.config import MemoryConfig, config

if TYPE_CHECKING:
    from mem0 import Memory


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

                from mem0 import Memory

                self._memory = Memory.from_config(self.memory_config.to_mem0_config())
            return self._memory

    def add(
        self,
        messages: str | list[dict[str, str]],
        *,
        user_id: str | None = None,
        agent_id: str | None = None,
        run_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        infer: bool = True,
    ) -> dict[str, Any]:
        memory = self._memory or self.load_memory()
        return memory.add(
            messages,
            user_id=user_id,
            agent_id=agent_id,
            run_id=run_id,
            metadata=metadata,
            infer=infer,
        )

    def search(
        self,
        query: str,
        *,
        user_id: str | None = None,
        agent_id: str | None = None,
        run_id: str | None = None,
        limit: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        memory = self._memory or self.load_memory()
        return memory.search(
            query,
            user_id=user_id,
            agent_id=agent_id,
            run_id=run_id,
            limit=limit,
            filters=filters,
        )


memory_service = MemoryService()
