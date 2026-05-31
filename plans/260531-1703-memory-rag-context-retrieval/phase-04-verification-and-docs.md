---
phase: 4
title: "Verification And Docs"
status: complete
priority: P2
effort: "3h"
dependencies: [1, 2, 3]
---

# Phase 4: Verification And Docs

## Context Links

- Runtime docs: `backend/README.md`
- Existing broad plan: `plans/260524-0736-personal-knowledge-brain/plan.md`
- Backend tests: `backend/tests/`

## Overview

Verify compile/tests, document the new memory retrieval behavior, and keep the broader knowledge-brain plan aligned with this focused blocker.

## Requirements

- Functional: all targeted and full backend tests pass.
- Non-functional: docs explain runtime knobs, fallback behavior, and what is still out of scope.

## Architecture

No new runtime architecture. This phase validates the implemented route and memory retrieval path end to end with deterministic test doubles.

## Related Code Files

- Modify: `backend/README.md`
- Modify: `plans/260524-0736-personal-knowledge-brain/plan.md` if dependency/status needs adjustment.
- Optional create: `docs/journals/260531-memory-rag-context-retrieval.md` after implementation.

## Implementation Steps

1. Run targeted tests during implementation:
   ```bash
   cd /home/mcs/Workspaces/ai-voice-first/backend
   uv run pytest tests/test_memory_service.py tests/test_assistant_service.py tests/test_app_routes.py -q
   ```
2. Run compile and full backend tests:
   ```bash
   cd /home/mcs/Workspaces/ai-voice-first/backend
   uv run python -m compileall .
   uv run pytest
   ```
3. Update `backend/README.md`.
   - Explain `ASSISTANT_USE_MEMORY_CONTEXT`.
   - Explain RAG context source: structured finance/person rows, optional embeddings, lexical fallback.
   - Explain recall questions are not stored as factual memories.
   - Add optional embedding env vars if implemented.
4. Update broad knowledge-brain plan.
   - Mark this focused plan as the blocker/foundation for smart retrieval.
   - Do not mark broad phases complete unless implementation actually covers them.
5. If docs impact is significant, add a short journal entry under `docs/journals/`.

## Todo List

- [x] Run targeted backend tests.
- [x] Run compileall.
- [x] Run full backend pytest.
- [x] Update README.
- [x] Sync broad plan dependency/status.

## Success Criteria

- [x] `uv run python -m compileall .` passes in `backend`.
- [x] `uv run pytest` passes in `backend`.
- [x] README documents memory retrieval behavior and env vars.
- [x] Broad knowledge-brain plan no longer hides this blocker.

## Risk Assessment

- Full tests may hit optional GPU/model paths. Mitigation: existing test env disables ASR/TTS preload; keep new tests offline.
- Docs may overpromise. Mitigation: describe only shipped RAG context behavior; keep reminders/insights out of scope.

## Security Considerations

Docs should warn that server-side memories are private user data and should run on trusted network until auth/rate limiting exist.

## Next Steps

After this plan lands, continue with broader knowledge-brain phases: better intent detection, reminders, insights, and UI.
