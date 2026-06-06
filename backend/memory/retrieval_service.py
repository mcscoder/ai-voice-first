from __future__ import annotations

from database import DatabaseEngine

from .config import env_int
from .retrieval_candidate_loader import RetrievalCandidateLoader
from .retrieval_records import EmbeddingProvider, MemorySearchResult, timestamp_score
from .text_similarity import tokenize


class MemoryRetrievalService:
    def __init__(
        self,
        engine: DatabaseEngine,
        *,
        embedding_service: EmbeddingProvider | None = None,
        max_candidates: int | None = None,
    ) -> None:
        self._engine = engine
        self._max_candidates = max_candidates or env_int(
            "MEMORY_RAG_MAX_CANDIDATES",
            300,
            minimum=1,
            maximum=5000,
        )
        self._candidate_loader = RetrievalCandidateLoader(
            max_candidates=self._max_candidates,
            embedding_service=embedding_service,
        )

    def search(self, user_id: str, query: str, limit: int = 5) -> list[MemorySearchResult]:
        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        candidates: dict[str, MemorySearchResult] = {}
        with self._engine.connection() as connection:
            person_names = self._candidate_loader.matching_people(connection, user_id, query)
            if self._candidate_loader.is_finance_query(query_tokens) or person_names:
                self._merge_candidates(
                    candidates,
                    self._candidate_loader.financial_candidates(
                        connection,
                        user_id,
                        person_names=person_names,
                        query_tokens=query_tokens,
                    ),
                )
            self._merge_candidates(
                candidates,
                self._candidate_loader.lexical_candidates(connection, user_id, query_tokens),
            )
            self._merge_candidates(
                candidates,
                self._candidate_loader.semantic_candidates(
                    connection,
                    user_id,
                    query,
                    query_tokens=query_tokens,
                ),
            )
            seed_results = self._rank_candidates(candidates)[:limit]
            self._merge_candidates(
                candidates,
                self._candidate_loader.linked_candidates(
                    connection,
                    user_id,
                    seed_results,
                ),
            )

        return self._rank_candidates(candidates)[:limit]

    def _rank_candidates(
        self,
        candidates: dict[str, MemorySearchResult],
    ) -> list[MemorySearchResult]:
        selected = [
            result
            for result in candidates.values()
            if result.score >= 1.0
        ]
        selected.sort(
            key=lambda result: (
                result.score,
                result.importance,
                timestamp_score(result.created_at),
            ),
            reverse=True,
        )
        return selected

    def _merge_candidates(
        self,
        target: dict[str, MemorySearchResult],
        results: list[MemorySearchResult],
    ) -> None:
        for result in results:
            existing = target.get(result.memory_id)
            if not existing or result.score > existing.score:
                target[result.memory_id] = result
