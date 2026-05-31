from __future__ import annotations

import asyncio
import json
import logging
import sqlite3
import uuid
from datetime import datetime, timezone

from database import bootstrap_schema, get_database_engine

from .context_builder import MemoryContextBuilder
from .embedding_service import MemoryEmbeddingService
from .entity_resolver import EntityResolver
from .extractor import MemoryExtractor
from .retrieval_records import EmbeddingProvider
from .retrieval_service import MemoryRetrievalService
from .schemas import ExtractedMemory, StoredMemory
from .text_similarity import memory_similarity, tokenize


logger = logging.getLogger(__name__)


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class MemoryService:
    def __init__(
        self,
        extractor: MemoryExtractor | None = None,
        entity_resolver: EntityResolver | None = None,
        embedding_service: EmbeddingProvider | None = None,
    ) -> None:
        self.extractor = extractor or MemoryExtractor()
        self.entity_resolver = entity_resolver or EntityResolver()
        self.embedding_service = embedding_service or MemoryEmbeddingService()
        self._engine = get_database_engine()
        self.retrieval_service = MemoryRetrievalService(
            self._engine,
            embedding_service=self.embedding_service,
        )
        self.context_builder = MemoryContextBuilder()

    def bootstrap(self) -> None:
        with self._engine.connection() as connection:
            bootstrap_schema(connection)

    async def build_context(self, user_id: str, transcript: str, limit: int = 5) -> str:
        return await asyncio.to_thread(self._build_context_sync, user_id, transcript, limit)

    def _build_context_sync(self, user_id: str, transcript: str, limit: int = 5) -> str:
        results = self.retrieval_service.search(user_id, transcript, limit)
        return self.context_builder.build(results)

    async def process_transcript(self, user_id: str, raw_text: str) -> StoredMemory:
        return await asyncio.to_thread(self.process_transcript_sync, user_id, raw_text)

    def process_transcript_sync(self, user_id: str, raw_text: str) -> StoredMemory:
        extracted = self.extractor.extract(raw_text)
        now = _utcnow()
        memory_id = str(uuid.uuid4())

        with self._engine.connection() as connection:
            self._ensure_user(connection, user_id)
            connection.execute(
                """
                INSERT INTO memories (
                    id, user_id, raw_text, processed_text, category, subcategory,
                    sentiment, importance, metadata_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    memory_id,
                    user_id,
                    raw_text,
                    extracted.processed_text,
                    extracted.category,
                    extracted.subcategory,
                    extracted.sentiment,
                    extracted.importance,
                    json.dumps(extracted.model_dump(), ensure_ascii=False),
                    now,
                    now,
                ),
            )

            resolved_people = self.entity_resolver.resolve_entities(
                connection,
                user_id,
                extracted.entities,
            )

            financial_person_id = self._match_financial_person_id(
                resolved_people,
                extracted.financial.person_name if extracted.financial else None,
            )
            if extracted.financial:
                connection.execute(
                    """
                    INSERT INTO financial_records (
                        id, user_id, memory_id, person_id, type, amount, currency,
                        status, due_date, settled_at, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(uuid.uuid4()),
                        user_id,
                        memory_id,
                        financial_person_id,
                        extracted.financial.type,
                        extracted.financial.amount,
                        extracted.financial.currency,
                        "pending",
                        extracted.financial.due_date,
                        None,
                        now,
                    ),
                )

            self._link_recent_memories(connection, user_id, memory_id, extracted)

        self._store_embedding(memory_id, extracted.processed_text)

        return StoredMemory(
            id=memory_id,
            user_id=user_id,
            raw_text=raw_text,
            processed_text=extracted.processed_text,
            category=extracted.category,
            subcategory=extracted.subcategory,
            sentiment=extracted.sentiment,
            importance=extracted.importance,
            metadata=extracted.model_dump(),
            created_at=now,
        )

    def _ensure_user(self, connection: sqlite3.Connection, user_id: str) -> None:
        now = _utcnow()
        connection.execute(
            """
            INSERT OR IGNORE INTO users (id, created_at, updated_at)
            VALUES (?, ?, ?)
            """,
            (user_id, now, now),
        )

    def _match_financial_person_id(
        self,
        resolved_people: list,
        person_name: str | None,
    ) -> str | None:
        if not resolved_people:
            return None
        if not person_name:
            return resolved_people[0].person.id
        normalized = person_name.strip().lower()
        for resolved in resolved_people:
            aliases = [resolved.person.name, *resolved.person.aliases]
            if any(alias.strip().lower() == normalized for alias in aliases):
                return resolved.person.id
        return resolved_people[0].person.id

    def _link_recent_memories(
        self,
        connection: sqlite3.Connection,
        user_id: str,
        memory_id: str,
        extracted: ExtractedMemory,
    ) -> None:
        rows = connection.execute(
            """
            SELECT id, processed_text
            FROM memories
            WHERE user_id = ? AND id != ?
            ORDER BY created_at DESC
            LIMIT 15
            """,
            (user_id, memory_id),
        ).fetchall()
        now = _utcnow()
        source_tokens = tokenize(extracted.processed_text)
        for row in rows:
            candidate_text = str(row["processed_text"])
            similarity = memory_similarity(
                extracted.processed_text,
                candidate_text,
                source_tokens=source_tokens,
            )
            if similarity < 0.72:
                continue
            connection.execute(
                """
                INSERT INTO memory_links (
                    id, source_memory_id, target_memory_id, link_type, strength, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    memory_id,
                    str(row["id"]),
                    "related",
                    similarity,
                    now,
                ),
            )

    async def list_recent_memories(self, user_id: str, limit: int = 20) -> list[StoredMemory]:
        return self._list_recent_memories_sync(user_id, limit)

    def _list_recent_memories_sync(self, user_id: str, limit: int) -> list[StoredMemory]:
        with self._engine.connection() as connection:
            rows = connection.execute(
                """
                SELECT id, raw_text, processed_text, category, subcategory,
                       sentiment, importance, metadata_json, created_at
                FROM memories
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (user_id, limit),
            ).fetchall()

        memories: list[StoredMemory] = []
        for row in rows:
            memories.append(
                StoredMemory(
                    id=str(row["id"]),
                    user_id=user_id,
                    raw_text=str(row["raw_text"]),
                    processed_text=str(row["processed_text"]),
                    category=str(row["category"]),
                    subcategory=row["subcategory"],
                    sentiment=float(row["sentiment"]),
                    importance=int(row["importance"]),
                    metadata=json.loads(row["metadata_json"]),
                    created_at=str(row["created_at"]),
                )
            )
        return memories

    def _store_embedding(
        self,
        memory_id: str,
        processed_text: str,
    ) -> None:
        if not self.embedding_service.is_enabled:
            return
        try:
            embedding = self.embedding_service.embed(processed_text)
            if not embedding:
                return
            now = _utcnow()
            with self._engine.connection() as connection:
                connection.execute(
                    """
                    INSERT OR REPLACE INTO memory_embeddings (
                        id, memory_id, embedding_json, model_name, created_at
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        str(uuid.uuid4()),
                        memory_id,
                        json.dumps(embedding),
                        self.embedding_service.model_name,
                        now,
                    ),
                )
        except Exception:
            logger.exception("Failed to store memory embedding.")
