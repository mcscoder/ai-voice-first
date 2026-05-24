from __future__ import annotations

import json

import httpx
import pytest

import database.engine as database_engine
from memory import MemoryExtractor, MemoryService


def _mock_memory_extraction_response(transcript: str) -> str:
    if "Minh nợ tao 60k" in transcript:
        return json.dumps(
            {
                "processed_text": "Minh nợ tao 60k",
                "category": "finance",
                "subcategory": "debt",
                "entities": [{"name": "Minh", "type": "person", "role": "mentioned"}],
                "financial": {
                    "amount": 60000,
                    "currency": "VND",
                    "type": "debt_owed",
                    "person_name": "Minh",
                    "due_date": None,
                },
                "sentiment": -0.2,
                "importance": 7,
                "emotional_tags": ["annoyed"],
                "time_references": [],
            },
            ensure_ascii=False,
        )

    return json.dumps(
        {
            "processed_text": transcript,
            "category": "general",
            "subcategory": None,
            "entities": [],
            "financial": None,
            "sentiment": 0.0,
            "importance": 1,
            "emotional_tags": [],
            "time_references": [],
        },
        ensure_ascii=False,
    )


def _memory_handler(request: httpx.Request) -> httpx.Response:
    payload = json.loads(request.content.decode())
    assert payload["model"] == "gemini-2.5-flash-lite"
    assert payload["messages"][0]["role"] == "system"
    assert "Return one JSON object only" in payload["messages"][0]["content"]

    transcript = payload["messages"][1]["content"].split("Transcript:\n", 1)[1].split("\n\n", 1)[0]
    return httpx.Response(
        200,
        json={
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": f"```json\n{_mock_memory_extraction_response(transcript)}\n```",
                    }
                }
            ]
        },
        request=request,
    )


@pytest.mark.anyio
async def test_memory_extractor_parses_llm_json_response():
    extractor = MemoryExtractor(
        base_url="http://assistant.local/v1",
        transport=httpx.MockTransport(_memory_handler),
    )

    memory = extractor.extract("Minh nợ tao 60k")

    assert memory.category == "finance"
    assert memory.financial is not None
    assert memory.financial.amount == 60000
    assert memory.entities
    assert memory.entities[0].name.lower().startswith("minh")


@pytest.mark.anyio
async def test_memory_service_persists_and_retrieves_context(tmp_path, monkeypatch):
    db_path = tmp_path / "brain.sqlite3"
    monkeypatch.setenv("KNOWLEDGE_BRAIN_DB_PATH", str(db_path))
    database_engine._engine = None

    extractor = MemoryExtractor(
        base_url="http://assistant.local/v1",
        transport=httpx.MockTransport(_memory_handler),
    )
    service = MemoryService(extractor=extractor)
    service.bootstrap()

    stored = await service.process_transcript("user-1", "Minh nợ tao 60k")
    assert stored.category == "finance"
    assert stored.processed_text == "Minh nợ tao 60k"

    recent = await service.list_recent_memories("user-1")
    assert len(recent) == 1
    assert recent[0].processed_text == "Minh nợ tao 60k"

    context = await service.build_context("user-1", "Minh nợ bao nhiêu?")
    assert "Minh nợ tao 60k" in context
