from __future__ import annotations

import os

import pytest

from assistant_service import VoiceAssistantService
from memory import MemoryExtractor


RUN_LIVE_LLM_SMOKE = os.getenv("RUN_LIVE_LLM_SMOKE") == "1"
ASSISTANT_BASE_URL = os.getenv("ASSISTANT_API_BASE_URL", "http://127.0.0.1:8317/v1")
ASSISTANT_API_KEY = os.getenv("ASSISTANT_API_KEY", "")
ASSISTANT_MODEL = os.getenv("ASSISTANT_MODEL", "gemini-2.5-flash-lite")


@pytest.mark.anyio
@pytest.mark.skipif(not RUN_LIVE_LLM_SMOKE, reason="live LLM smoke test disabled")
async def test_live_assistant_service_requests_llm_server():
    service = VoiceAssistantService(
        base_url=ASSISTANT_BASE_URL,
        api_key=ASSISTANT_API_KEY,
        model=ASSISTANT_MODEL,
        timeout_seconds=30,
    )

    reply = await service.complete(
        "Reply with exactly: pong",
        "en",
    )

    assert reply


@pytest.mark.anyio
@pytest.mark.skipif(not RUN_LIVE_LLM_SMOKE, reason="live LLM smoke test disabled")
async def test_live_memory_extractor_requests_llm_server():
    extractor = MemoryExtractor(
        base_url=ASSISTANT_BASE_URL,
        api_key=ASSISTANT_API_KEY,
        model=ASSISTANT_MODEL,
        timeout_seconds=30,
    )

    memory = extractor.extract("Minh nợ tao 60k")

    assert memory.processed_text
    assert memory.category in {"finance", "work", "relationship", "plan", "emotion", "general"}
