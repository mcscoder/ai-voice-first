from __future__ import annotations

import json
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from difflib import SequenceMatcher

from database import bootstrap_schema, get_database_engine

from .entity_resolver import EntityResolver
from .extractor import MemoryExtractor
from .schemas import ExtractedMemory, StoredMemory


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class MemoryService:
    def __init__(
        self,
        extractor: MemoryExtractor | None = None,
        entity_resolver: EntityResolver | None = None,
    ) -> None:
        self.extractor = extractor or MemoryExtractor()
        self.entity_resolver = entity_resolver or EntityResolver()
        self._engine = get_database_engine()

    def bootstrap(self) -> None:
        with self._engine.connection() as connection:
            bootstrap_schema(connection)

    async def build_context(self, user_id: str, transcript: str, limit: int = 5) -> str:
        return self._build_context_sync(user_id, transcript, limit)

    async def process_transcript(self, user_id: str, raw_text: str) -> StoredMemory:
        return self.process_transcript_sync(user_id, raw_text)

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

    def _build_context_sync(self, user_id: str, transcript: str, limit: int) -> str:
        query_tokens = self._tokenize(transcript)
        with self._engine.connection() as connection:
            rows = connection.execute(
                """
                SELECT m.id, m.processed_text, m.category, m.sentiment, m.importance,
                       m.created_at, p.name AS person_name, f.amount, f.currency, f.status
                FROM memories m
                LEFT JOIN financial_records f ON f.memory_id = m.id
                LEFT JOIN people p ON p.id = f.person_id
                WHERE m.user_id = ?
                ORDER BY m.created_at DESC
                LIMIT 30
                """,
                (user_id,),
            ).fetchall()

        scored: list[tuple[float, str]] = []
        for row in rows:
            text = str(row["processed_text"])
            haystack = f"{text} {row['category']} {row['person_name'] or ''}".lower()
            score = self._score_haystack(query_tokens, haystack)
            if score <= 0:
                continue

            amount = row["amount"]
            person = row["person_name"]
            snippets = [f"- {text} ({row['category']}, {row['created_at']})"]
            if person or amount is not None:
                details: list[str] = []
                if person:
                    details.append(f"person={person}")
                if amount is not None:
                    details.append(f"amount={amount:g} {row['currency']}")
                if details:
                    snippets[-1] += f" [{', '.join(details)}]"
            scored.append((score, snippets[0]))

        scored.sort(key=lambda item: item[0], reverse=True)
        selected = [line for _, line in scored[:limit]]
        if not selected:
            return ""
        return "\n".join(["[MEMORY CONTEXT]", *selected, "[/MEMORY CONTEXT]"])

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
        source_tokens = self._tokenize(extracted.processed_text)
        for row in rows:
            candidate_text = str(row["processed_text"])
            similarity = self._memory_similarity(
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

    def _tokenize(self, text: str) -> set[str]:
        return {
            token.lower()
            for token in re.findall(r"[\wÀ-ỹ']+", text)
            if len(token) > 2
        }

    def _score_haystack(self, query_tokens: set[str], haystack: str) -> float:
        if not query_tokens:
            return 0.0

        score = sum(1.0 for token in query_tokens if token in haystack)
        if any(token in query_tokens for token in {"nợ", "tiền", "trả", "debt", "money"}):
            if "finance" in haystack or "money" in haystack:
                score += 2.0
        if any(token in query_tokens for token in {"mai", "hôm nay", "tuần", "month", "plan"}):
            if "plan" in haystack:
                score += 1.0
        return score

    def _memory_similarity(
        self,
        source_text: str,
        candidate_text: str,
        *,
        source_tokens: set[str],
    ) -> float:
        candidate_tokens = self._tokenize(candidate_text)
        union = source_tokens | candidate_tokens
        overlap = 0.0 if not union else len(source_tokens & candidate_tokens) / len(union)
        text_ratio = SequenceMatcher(
            None,
            source_text.lower(),
            candidate_text.lower(),
        ).ratio()
        return max(overlap, text_ratio)
