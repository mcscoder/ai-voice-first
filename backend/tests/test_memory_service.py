from __future__ import annotations

import json

import httpx
import pytest

import database.engine as database_engine
from memory import ExtractedEntity, ExtractedFinancial, ExtractedMemory, MemoryExtractor, MemoryService


class StaticExtractor:
    def extract(self, transcript: str) -> ExtractedMemory:
        if "Minh nợ tao 60k" in transcript:
            return ExtractedMemory(
                processed_text="Minh nợ tao 60k",
                category="finance",
                subcategory="debt",
                entities=[ExtractedEntity(name="Minh")],
                financial=ExtractedFinancial(
                    amount=60000,
                    currency="VND",
                    type="debt_owed",
                    person_name="Minh",
                ),
                sentiment=-0.2,
                importance=7,
            )
        if "Lan nợ tao 120k" in transcript:
            return ExtractedMemory(
                processed_text="Lan nợ tao 120k",
                category="finance",
                subcategory="debt",
                entities=[ExtractedEntity(name="Lan")],
                financial=ExtractedFinancial(
                    amount=120000,
                    currency="VND",
                    type="debt_owed",
                    person_name="Lan",
                ),
                sentiment=-0.1,
                importance=6,
            )
        if "tao nợ Nam 30k" in transcript:
            return ExtractedMemory(
                processed_text="tao nợ Nam 30k",
                category="finance",
                subcategory="debt",
                entities=[ExtractedEntity(name="Nam")],
                financial=ExtractedFinancial(
                    amount=30000,
                    currency="VND",
                    type="debt_owed_to",
                    person_name="Nam",
                ),
                importance=5,
            )
        if "ăn phở hết 40k" in transcript:
            return ExtractedMemory(
                processed_text="ăn phở hết 40k",
                category="finance",
                subcategory="expense",
                financial=ExtractedFinancial(
                    amount=40000,
                    currency="VND",
                    type="expense",
                ),
                importance=3,
            )
        if "Quán cà phê yên tĩnh ở quận 1" in transcript:
            return ExtractedMemory(
                processed_text="Quán cà phê yên tĩnh ở quận 1",
                category="general",
                importance=5,
            )
        return ExtractedMemory(
            processed_text=transcript,
            category="general",
            importance=1,
        )


class FakeEmbeddingService:
    is_enabled = True
    model_name = "fake-embedding"

    def embed(self, text: str) -> list[float] | None:
        if "Quán cà phê" in text or "chỗ làm việc tập trung" in text:
            return [1.0, 0.0]
        return [0.0, 1.0]


def _memory_service(tmp_path, monkeypatch, *, embedding_service=None) -> MemoryService:
    db_path = tmp_path / "brain.sqlite3"
    monkeypatch.setenv("KNOWLEDGE_BRAIN_DB_PATH", str(db_path))
    database_engine._engine = None

    service = MemoryService(
        extractor=StaticExtractor(),
        embedding_service=embedding_service,
    )
    service.bootstrap()
    return service


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
async def test_memory_extractor_prompt_log_writes_transcript(monkeypatch, tmp_path):
    prompt_log = tmp_path / "assistant_prompt.log"
    monkeypatch.setenv("ASSISTANT_PROMPT_LOG_FILE", str(prompt_log))
    extractor = MemoryExtractor(
        base_url="http://assistant.local/v1",
        transport=httpx.MockTransport(_memory_handler),
    )

    extractor.extract("Minh nợ tao 60k")

    log_text = prompt_log.read_text(encoding="utf-8")
    assert "Minh nợ tao 60k" in log_text
    assert "[MEMORY EXTRACTION PAYLOAD REDACTED]" not in log_text


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


@pytest.mark.anyio
async def test_memory_context_retrieves_old_relevant_memory_after_recent_noise(
    tmp_path,
    monkeypatch,
):
    service = _memory_service(tmp_path, monkeypatch)

    await service.process_transcript("user-1", "Minh nợ tao 60k")
    for index in range(35):
        await service.process_transcript("user-1", f"Ghi chú linh tinh số {index}")

    context = await service.build_context("user-1", "Minh nợ bao nhiêu?")

    assert "Minh nợ tao 60k" in context


@pytest.mark.anyio
async def test_memory_context_uses_financial_records_for_open_debt_query(
    tmp_path,
    monkeypatch,
):
    service = _memory_service(tmp_path, monkeypatch)

    await service.process_transcript("user-1", "Minh nợ tao 60k")
    await service.process_transcript("user-1", "Lan nợ tao 120k")
    await service.process_transcript("user-1", "tao nợ Nam 30k")
    await service.process_transcript("user-1", "ăn phở hết 40k")
    await service.process_transcript("user-1", "mai gặp Minh")

    context = await service.build_context("user-1", "ai nợ tao tiền?")

    assert "Minh nợ tao 60k" in context
    assert "Lan nợ tao 120k" in context
    assert "tao nợ Nam 30k" not in context
    assert "ăn phở hết 40k" not in context
    assert "mai gặp Minh" not in context

    terse_context = await service.build_context("user-1", "ai nợ?")
    assert "Minh nợ tao 60k" in terse_context
    assert "Lan nợ tao 120k" in terse_context
    assert "tao nợ Nam 30k" not in terse_context
    assert "mai gặp Minh" not in terse_context


@pytest.mark.anyio
async def test_memory_context_returns_empty_for_unrelated_query(tmp_path, monkeypatch):
    service = _memory_service(tmp_path, monkeypatch)
    await service.process_transcript("user-1", "Minh nợ tao 60k")

    context = await service.build_context("user-1", "thời tiết hôm nay thế nào?")

    assert context == ""


@pytest.mark.anyio
async def test_memory_context_expands_from_relevant_seed_to_linked_memories(
    tmp_path,
    monkeypatch,
):
    service = _memory_service(tmp_path, monkeypatch)
    seed = await service.process_transcript("user-1", "Project Atlas deadline Friday")
    linked = await service.process_transcript("user-1", "Budget approval moved to Monday")
    with service._engine.connection() as connection:
        connection.execute(
            """
            INSERT INTO memory_links (
                id, source_memory_id, target_memory_id, link_type, strength, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "link-1",
                seed.id,
                linked.id,
                "related",
                0.9,
                "2026-06-01T00:00:00+00:00",
            ),
        )

    context = await service.build_context("user-1", "deadline Friday")

    assert "Project Atlas deadline Friday" in context
    assert "Budget approval moved to Monday" in context


@pytest.mark.anyio
async def test_memory_context_can_use_stored_embeddings(tmp_path, monkeypatch):
    service = _memory_service(
        tmp_path,
        monkeypatch,
        embedding_service=FakeEmbeddingService(),
    )
    await service.process_transcript("user-1", "Quán cà phê yên tĩnh ở quận 1")

    context = await service.build_context("user-1", "chỗ làm việc tập trung")

    assert "Quán cà phê yên tĩnh ở quận 1" in context
