---
phase: 2
title: "RAG Retrieval Core"
status: complete
priority: P1
effort: "8h"
dependencies: [1]
---

# Phase 2: RAG Retrieval Core

## Context Links

- Current service: `backend/memory/memory_service.py`
- Current schema: `backend/database/models.py`
- Existing extraction: `backend/memory/extractor.py`, `backend/memory/schemas.py`
- Regression tests from Phase 1

## Overview

Build a real retrieval layer under the existing memory service API. Retrieval must search stored memories by query meaning, structured facts, and lexical fallback, then format compact context for the assistant.

## Key Insights

- Keep `MemoryService.build_context(user_id, transcript, limit)` as the public API.
- Avoid making `memory_service.py` larger. It is already above the 200-line guidance.
- SQLite is current reality. Do not plan pgvector migration here.
- Embeddings should improve ranking, but structured debt queries must work without embeddings.

## Requirements

- Functional: retrieve relevant memories across the full user history, not only newest rows.
- Functional: use financial records for debt/money queries.
- Functional: use person aliases when the query mentions a known person.
- Functional: optionally use semantic embeddings when available.
- Non-functional: bounded candidate reads; stable behavior if embedding generation fails.

## Architecture

```
query transcript
  -> MemoryRetrievalService.search(user_id, query, limit)
      -> query hints: tokens, debt terms, person aliases, category hints
      -> structured candidates: financial_records, people, categories
      -> semantic candidates: memory_embeddings cosine similarity if enabled
      -> lexical fallback: token overlap over bounded candidates
      -> merge + rerank: structured boosts, similarity, importance, recency
  -> MemoryContextBuilder.format(results)
  -> assistant system prompt
```

## Related Code Files

- Create: `backend/memory/retrieval_service.py` - search orchestration and scoring.
- Create: `backend/memory/context_builder.py` - token-budget-aware context formatting.
- Create: `backend/memory/embedding_service.py` - embedding generation/storage interface.
- Modify: `backend/memory/memory_service.py` - delegate context building and store embeddings for new memories.
- Modify: `backend/memory/__init__.py` - export new services if tests need imports.
- Modify: `backend/database/models.py` - add indexes only if needed; avoid schema churn.
- Modify: `backend/pyproject.toml` - add embedding dependency only if implementation chooses local embeddings.

## Implementation Steps

1. Extract context-building out of `memory_service.py`.
   - Add `MemoryRetrievalService`.
   - Move tokenization/scoring helpers there or into small private helpers.
   - Keep `MemoryService.build_context()` as a thin delegator.
2. Implement structured retrieval.
   - Detect debt/money queries with Vietnamese and English terms: `nợ`, `tiền`, `trả`, `debt`, `money`, `owe`.
   - Query `financial_records` joined to `memories` and `people`.
   - Boost pending records and exact person alias matches.
3. Implement lexical fallback over bounded candidates.
   - Use all structured matches plus a bounded memory candidate set, not only latest 30.
   - Config: `MEMORY_RAG_MAX_CANDIDATES`, default around 300.
   - Score token overlap, category hints, importance, and modest recency.
4. Implement optional semantic retrieval.
   - Add `EmbeddingService` with `embed(text) -> list[float]`.
   - Store memory embeddings in existing `memory_embeddings`.
   - Compute cosine similarity in Python for SQLite.
   - If dependency/model unavailable, log and continue with structured + lexical retrieval.
5. Store embeddings for new memories.
   - After memory insert, call embedding service if enabled.
   - Do not fail memory storage if embedding fails.
6. Build context formatting.
   - Include memory text, category, date, person, amount/status when available.
   - Deduplicate by memory id.
   - Respect `limit` and a simple character budget.
   - Return empty string when score threshold not met.

## Todo List

- [x] Create retrieval service.
- [x] Create context builder.
- [x] Add optional embedding service.
- [x] Wire `MemoryService.build_context()` to retrieval.
- [x] Keep `memory_service.py` smaller or split enough to stop growth.

## Success Criteria

- [x] Older relevant memories can be retrieved beyond the latest 30 rows.
- [x] Debt query returns finance rows through structured search.
- [x] Semantic search path covered with a fake embedding provider in tests.
- [x] Embedding failures do not break voice assistant responses.
- [x] `MemoryService.build_context()` keeps same signature.

## Risk Assessment

- Heavy embedding dependency can slow installs. Mitigation: keep provider optional and fallback-safe.
- SQLite vector search is not scalable. Mitigation: bounded candidate scan is acceptable for local personal memory MVP; future pgvector remains separate plan.
- Ranking can overfit tests. Mitigation: test behavior, not exact score values.

## Security Considerations

Memory context is private user data. Never log full context at info level. Redact memory context in prompt logs.

## Next Steps

Integrate context into assistant route and prevent query pollution.
