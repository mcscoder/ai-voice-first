---
title: "Memory RAG Context Retrieval"
description: "Replace recent-message memory context with query-driven retrieval over stored memories before assistant generation."
status: complete
priority: P1
effort: 18h
issue:
branch: faster-whisper
tags: [backend, memory, rag, database, assistant]
blockedBy: []
blocks: [260524-0736-personal-knowledge-brain]
created: 2026-05-31
---

# Memory RAG Context Retrieval

## Overview

Fix assistant memory context. Current backend stores memories, people, finance rows, and a `memory_embeddings` table, but assistant context is built from the newest rows first and lexical scoring. This plan replaces that with query-driven retrieval: structured memory search, optional semantic embedding search, lexical fallback, context formatting, and route tests proving old relevant memories beat recent irrelevant ones.

## Scope Challenge

- Existing code: `MemoryService`, SQLite schema, entity resolver, assistant prompt injection, tests.
- Minimum changes: retrieval/context path only. No Flutter, reminders, insights, PostgreSQL migration, or full command router.
- Complexity: expected 6-8 backend files, 2-3 small new memory modules. Keep touched Python modules under 200 lines where practical.
- Selected mode: hold scope. Implement RAG context well before expanding the brain features.

## Cross-Plan Dependencies

| Relationship | Plan | Status |
|-------------|------|--------|
| Blocks | `260524-0736-personal-knowledge-brain` | pending |

The broad knowledge-brain plan assumes smart retrieval. This focused plan should land first because it corrects the current behavior.

## Phases

| Phase | Name | Status |
|-------|------|--------|
| 1 | [Current Behavior Baseline](./phase-01-current-behavior-baseline.md) | Complete |
| 2 | [RAG Retrieval Core](./phase-02-rag-retrieval-core.md) | Complete |
| 3 | [Assistant Integration](./phase-03-assistant-integration.md) | Complete |
| 4 | [Verification And Docs](./phase-04-verification-and-docs.md) | Complete |

## Dependencies

- Current backend remains FastAPI + SQLite. Do not migrate to PostgreSQL in this plan.
- Reuse `ASSISTANT_USE_MEMORY_CONTEXT`; evaluate it at request time, not import time.
- Add a real embedding provider only behind a small interface. Use structured + lexical retrieval as fallback.

## Success Criteria

- Query `Minh nợ bao nhiêu?` retrieves an older Minh debt memory even after many newer unrelated memories.
- Query `ai nợ tao tiền?` uses financial records, not only token overlap with recent messages.
- Assistant prompt receives only relevant memory context, or `None` if no relevant memory found.
- Recall questions are not stored back as factual memories.
- `cd backend && uv run python -m compileall . && uv run pytest` passes.

## Cook Command

```bash
/ck:cook /home/mcs/Workspaces/ai-voice-first/plans/260531-1703-memory-rag-context-retrieval/plan.md
```

> Best practice: run `/clear` before implementation.

## Unresolved Questions

None. Assumption: keep SQLite for now and make semantic embeddings optional/fallback-safe.
