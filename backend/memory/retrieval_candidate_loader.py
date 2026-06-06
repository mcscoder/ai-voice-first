from __future__ import annotations

import json
import logging
import re
import sqlite3

from .retrieval_records import (
    CATEGORY_HINTS,
    FINANCE_QUERY_TERMS,
    EmbeddingProvider,
    MemorySearchResult,
    row_to_result,
)
from .text_similarity import cosine_similarity, tokenize


logger = logging.getLogger(__name__)


class RetrievalCandidateLoader:
    def __init__(
        self,
        *,
        max_candidates: int,
        embedding_service: EmbeddingProvider | None = None,
    ) -> None:
        self._max_candidates = max_candidates
        self._embedding_service = embedding_service

    def matching_people(
        self,
        connection: sqlite3.Connection,
        user_id: str,
        query: str,
    ) -> set[str]:
        normalized_query = query.lower()
        rows = connection.execute(
            """
            SELECT name, aliases_json
            FROM people
            WHERE user_id = ?
            ORDER BY interaction_count DESC, updated_at DESC
            LIMIT ?
            """,
            (user_id, self._max_candidates),
        ).fetchall()
        matches: set[str] = set()
        for row in rows:
            aliases = [str(row["name"]), *json.loads(row["aliases_json"])]
            if any(_alias_matches_query(alias, normalized_query) for alias in aliases):
                matches.add(str(row["name"]).lower())
        return matches

    def financial_candidates(
        self,
        connection: sqlite3.Connection,
        user_id: str,
        *,
        person_names: set[str],
        query_tokens: set[str],
    ) -> list[MemorySearchResult]:
        rows = connection.execute(
            """
            SELECT m.id, m.processed_text, m.category, m.importance, m.created_at,
                   p.name AS person_name, f.type AS financial_type, f.amount,
                   f.currency, f.status
            FROM financial_records f
            JOIN memories m ON m.id = f.memory_id
            LEFT JOIN people p ON p.id = f.person_id
            WHERE f.user_id = ? AND f.type = 'debt_owed' AND f.status = 'pending'
            ORDER BY f.created_at DESC
            LIMIT ?
            """,
            (user_id, self._max_candidates),
        ).fetchall()
        results: list[MemorySearchResult] = []
        finance_query = self.is_finance_query(query_tokens)
        for row in rows:
            person_name = str(row["person_name"]) if row["person_name"] else None
            person_match = bool(person_name and person_name.lower() in person_names)
            if person_names and not person_match and not finance_query:
                continue
            score = 4.0 if finance_query else 1.5
            if person_match:
                score += 3.0
            if row["status"] == "pending":
                score += 2.0
            results.append(row_to_result(row, score=score))
        return results

    def lexical_candidates(
        self,
        connection: sqlite3.Connection,
        user_id: str,
        query_tokens: set[str],
    ) -> list[MemorySearchResult]:
        rows = connection.execute(
            """
            SELECT m.id, m.processed_text, m.category, m.importance, m.created_at,
                   p.name AS person_name, f.type AS financial_type, f.amount,
                   f.currency, f.status
            FROM memories m
            LEFT JOIN financial_records f ON f.memory_id = m.id
            LEFT JOIN people p ON p.id = f.person_id
            WHERE m.user_id = ?
            ORDER BY m.importance DESC, m.created_at DESC
            LIMIT ?
            """,
            (user_id, self._max_candidates),
        ).fetchall()
        results: list[MemorySearchResult] = []
        finance_query = self.is_finance_query(query_tokens)
        for row in rows:
            if finance_query and not _is_open_debt_row(row):
                continue
            haystack_tokens = tokenize(
                f"{row['processed_text']} {row['category']} {row['person_name'] or ''}"
            )
            score = float(len(query_tokens & haystack_tokens))
            score += self._category_score(str(row["category"]), query_tokens)
            if score <= 0:
                continue
            score += min(int(row["importance"]), 10) * 0.05
            results.append(row_to_result(row, score=score))
        return results

    def semantic_candidates(
        self,
        connection: sqlite3.Connection,
        user_id: str,
        query: str,
        *,
        query_tokens: set[str],
    ) -> list[MemorySearchResult]:
        if not self._embedding_service or not self._embedding_service.is_enabled:
            return []
        try:
            query_embedding = self._embedding_service.embed(query)
        except Exception:
            logger.exception("Failed to embed memory retrieval query.")
            return []
        if not query_embedding:
            return []

        rows = connection.execute(
            """
            SELECT m.id, m.processed_text, m.category, m.importance, m.created_at,
                   e.embedding_json, p.name AS person_name,
                   f.type AS financial_type, f.amount, f.currency, f.status
            FROM memory_embeddings e
            JOIN memories m ON m.id = e.memory_id
            LEFT JOIN financial_records f ON f.memory_id = m.id
            LEFT JOIN people p ON p.id = f.person_id
            WHERE m.user_id = ?
            ORDER BY m.importance DESC, m.created_at DESC
            LIMIT ?
            """,
            (user_id, self._max_candidates),
        ).fetchall()
        results: list[MemorySearchResult] = []
        finance_query = self.is_finance_query(query_tokens)
        for row in rows:
            if finance_query and not _is_open_debt_row(row):
                continue
            try:
                similarity = cosine_similarity(
                    query_embedding,
                    json.loads(row["embedding_json"]),
                )
            except (TypeError, ValueError):
                continue
            if similarity >= 0.62:
                results.append(row_to_result(row, score=similarity * 5.0))
        return results

    def linked_candidates(
        self,
        connection: sqlite3.Connection,
        user_id: str,
        seed_results: list[MemorySearchResult],
    ) -> list[MemorySearchResult]:
        if not seed_results:
            return []

        seed_scores = {result.memory_id: result.score for result in seed_results}
        seed_ids = list(seed_scores)
        placeholders = ", ".join("?" for _ in seed_ids)
        link_rows = connection.execute(
            f"""
            SELECT source_memory_id, target_memory_id, strength
            FROM memory_links
            WHERE source_memory_id IN ({placeholders})
               OR target_memory_id IN ({placeholders})
            ORDER BY strength DESC
            LIMIT ?
            """,
            (*seed_ids, *seed_ids, self._max_candidates),
        ).fetchall()

        related_scores: dict[str, float] = {}
        for row in link_rows:
            source_id = str(row["source_memory_id"])
            target_id = str(row["target_memory_id"])
            strength = float(row["strength"])
            if source_id in seed_scores:
                related_id = target_id
                seed_score = seed_scores[source_id]
            else:
                related_id = source_id
                seed_score = seed_scores[target_id]
            if related_id in seed_scores:
                continue
            score = max(1.0, seed_score * strength * 0.85)
            related_scores[related_id] = max(score, related_scores.get(related_id, 0.0))

        if not related_scores:
            return []

        related_ids = list(related_scores)
        related_placeholders = ", ".join("?" for _ in related_ids)
        rows = connection.execute(
            f"""
            SELECT m.id, m.processed_text, m.category, m.importance, m.created_at,
                   p.name AS person_name, f.type AS financial_type, f.amount,
                   f.currency, f.status
            FROM memories m
            LEFT JOIN financial_records f ON f.memory_id = m.id
            LEFT JOIN people p ON p.id = f.person_id
            WHERE m.user_id = ? AND m.id IN ({related_placeholders})
            ORDER BY m.importance DESC, m.created_at DESC
            """,
            (user_id, *related_ids),
        ).fetchall()
        return [
            row_to_result(row, score=related_scores[str(row["id"])])
            for row in rows
        ]

    def is_finance_query(self, query_tokens: set[str]) -> bool:
        return bool(query_tokens & FINANCE_QUERY_TERMS)

    def _category_score(self, category: str, query_tokens: set[str]) -> float:
        terms = CATEGORY_HINTS.get(category, set())
        return 1.25 if query_tokens & terms else 0.0


def _alias_matches_query(alias: str, normalized_query: str) -> bool:
    normalized_alias = " ".join(alias.strip().lower().split())
    if not normalized_alias:
        return False
    if " " not in normalized_alias:
        return normalized_alias in tokenize(normalized_query)
    pattern = rf"(?<!\w){re.escape(normalized_alias)}(?!\w)"
    return bool(re.search(pattern, normalized_query))


def _is_open_debt_row(row: sqlite3.Row) -> bool:
    if "financial_type" not in row.keys() or row["financial_type"] is None:
        return False
    return row["financial_type"] == "debt_owed" and row["status"] == "pending"
