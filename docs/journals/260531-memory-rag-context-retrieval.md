# Memory RAG Context Retrieval

**Date**: 2026-05-31
**Severity**: Medium
**Component**: `backend/memory`, `backend/assistant_routes.py`, `backend/assistant_service.py`
**Status**: Resolved

## What Happened

Replaced assistant memory context from recent-row loading with query-driven retrieval.
The assistant now searches stored memories before generation instead of relying on the
latest messages.

## Technical Details

- Added retrieval over structured finance/person rows, lexical candidates, and optional embeddings.
- Kept SQLite and the existing `MemoryService.build_context()` API.
- Added a context formatter with a small character budget and duplicate filtering.
- Added runtime checks for `ASSISTANT_USE_MEMORY_CONTEXT` and `ASSISTANT_STORE_MEMORIES`.
- Memory access can be restricted to loopback requests with `ASSISTANT_ALLOW_REMOTE_MEMORY_CONTEXT=false`.
- Redacted memory context from prompt logs.
- Framed retrieved memory as untrusted user data in assistant prompts.
- Skipped storing pure recall questions such as `Minh nợ bao nhiêu?` as factual memories.
- Added prompt guardrails to use memory context only when relevant.

## Validation

- `uv run pytest tests/test_memory_service.py tests/test_app_routes.py tests/test_assistant_service.py -q` passed: 31 passed.
- `uv run python -m compileall .` passed.
- `uv run pytest` passed: 47 passed, 4 skipped.

## Lessons Learned

- The existing `memory_embeddings` table was enough for an optional semantic path; no database migration needed.
- Finance recall must use structured rows because many Vietnamese debt questions have weak lexical overlap.
- Recall-question storage needs a deterministic gate before any broader intent router is introduced.

## Unresolved Questions

None.
