---
phase: 1
title: "Current Behavior Baseline"
status: complete
priority: P1
effort: "3h"
dependencies: []
---

# Phase 1: Current Behavior Baseline

## Context Links

- Source request: `brainstorm.md`
- Backend docs: `backend/README.md`
- Current service: `backend/memory/memory_service.py`
- Current assistant route: `backend/assistant_routes.py`
- Existing tests: `backend/tests/test_memory_service.py`, `backend/tests/test_app_routes.py`

## Overview

Create failing tests for the real bug before changing retrieval: recent irrelevant memories should not beat older relevant memories, and recall questions should not be stored as facts.

## Key Insights

- `MemoryService._build_context_sync()` fetches latest 30 memories, then lexical scores. Older relevant facts can disappear.
- `memory_embeddings` table exists but is unused.
- `assistant_routes.py` stores every transcript after response; recall questions can pollute future context.
- `ASSISTANT_USE_MEMORY_CONTEXT` is read at import time, making runtime/test toggles awkward.

## Requirements

- Functional: tests prove retrieval is query-driven, not recency-driven.
- Non-functional: tests avoid live LLM, ASR, TTS, or GPU dependencies.

## Architecture

Use tmp SQLite via `KNOWLEDGE_BRAIN_DB_PATH` and fake extractors. Seed memories directly through `MemoryService` or database inserts when exact timestamps/cases matter. Keep tests deterministic.

## Related Code Files

- Modify: `backend/tests/test_memory_service.py`
- Modify: `backend/tests/test_app_routes.py`
- Read only: `backend/memory/memory_service.py`, `backend/assistant_routes.py`

## Implementation Steps

1. Add regression test: create one old finance memory for Minh, then more than 30 newer unrelated memories. Query `Minh nợ bao nhiêu?`. Expected context includes Minh debt.
2. Add structured finance query test: with multiple debt records, query `ai nợ tao tiền?`. Expected context includes pending debt summaries even when query has no person name.
3. Add no-result test: unrelated query returns empty context, not newest memories.
4. Add recall-question storage test: a pure question like `Minh nợ bao nhiêu?` must not be persisted as a factual memory.
5. Add assistant route test for memory context enabled. Monkeypatch retrieval to return context and assert `assistant_service.complete(..., memory_context=...)`.
6. Run targeted tests and confirm at least the recency regression fails before Phase 2.

## Todo List

- [x] Add memory service regression tests.
- [x] Add assistant route context test.
- [x] Document current failures in test comments only where useful.

## Success Criteria

- [x] Tests fail against current recency-first implementation for the right reason.
- [x] No test requires live network, model download, ASR, or TTS.
- [x] Test data isolated per test via tmp SQLite path and engine reset.

## Risk Assessment

- Import-time env flags can make tests misleading. Mitigation: Phase 3 moves flag evaluation to request time; Phase 1 can monkeypatch module values only as a temporary red test.
- Direct DB seeding can couple tests to schema. Mitigation: prefer service calls unless timestamps or bulk rows require direct inserts.

## Security Considerations

Use synthetic memory content only. Do not read or write `.env`.

## Next Steps

Implement retrieval core once tests define expected behavior.
