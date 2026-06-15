from __future__ import annotations

import os
from pathlib import Path

import pytest

from app.core.config import MemoryConfig
from app.services.memory.service import MemoryService


def test_memory_service_adds_and_searches_real_mem0_memory(tmp_path: Path) -> None:
    service = MemoryService(MemoryConfig(data_dir=tmp_path))
    user_id = "integration-user"
    memory_text = "The user prefers Vietnamese iced coffee in the morning."

    add_result = service.add(
        [{"role": "user", "content": memory_text}],
        user_id=user_id,
        infer=False,
    )
    search_result = service.search(
        "What coffee does the user prefer?",
        user_id=user_id,
        limit=1,
    )

    assert add_result["results"][0]["memory"] == memory_text
    assert search_result["results"]
    assert search_result["results"][0]["memory"] == memory_text


def test_memory_service_extracts_memory_with_gemini(tmp_path: Path) -> None:
    service = MemoryService(MemoryConfig(data_dir=tmp_path))
    user_id = "gemini-integration-user"

    add_result = service.add(
        [
            {
                "role": "user",
                "content": "My preferred planning drink is jasmine green tea.",
            },
        ],
        user_id=user_id,
    )
    search_result = service.search(
        "What drink does the user prefer for planning?",
        user_id=user_id,
        limit=3,
    )

    memories = [item["memory"] for item in search_result["results"]]

    assert add_result["results"]
    assert any("jasmine" in memory.lower() for memory in memories)
