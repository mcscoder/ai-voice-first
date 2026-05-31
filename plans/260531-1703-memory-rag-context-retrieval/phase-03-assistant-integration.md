---
phase: 3
title: "Assistant Integration"
status: complete
priority: P1
effort: "4h"
dependencies: [2]
---

# Phase 3: Assistant Integration

## Context Links

- Assistant route: `backend/assistant_routes.py`
- Assistant prompt builder: `backend/assistant_service.py`, `backend/personality/prompt_builder.py`
- Memory service API from Phase 2
- Backend README assistant settings

## Overview

Wire the new retrieval layer into the voice assistant request path without changing the external API. Also stop recall questions from being stored as factual memories.

## Key Insights

- Current route already calls `MemoryService().build_context("local-user", transcript)`.
- Current `store_memories_after_response` and `use_memory_context` are import-time globals.
- Current background storage stores every transcript, including questions.

## Requirements

- Functional: assistant receives relevant context before completion when memory context is enabled.
- Functional: assistant receives `None` when no relevant context exists.
- Functional: pure recall questions are not stored as memories.
- Non-functional: no route response-shape changes; preserve `audio/mpeg` contract.

## Architecture

```
audio -> ASR transcript
  -> should_use_memory_context()
  -> MemoryService.build_context(local-user, transcript)
  -> assistant_service.complete(..., memory_context=context or None)
  -> TTS audio response
  -> if should_store_memory(transcript): background memory extraction
```

## Related Code Files

- Modify: `backend/assistant_routes.py`
- Modify: `backend/assistant_service.py`
- Modify: `backend/personality/prompt_builder.py`
- Create or modify: `backend/memory/intent.py` if storage gating needs a small helper.
- Modify: `backend/tests/test_app_routes.py`
- Modify: `backend/tests/test_assistant_service.py`

## Implementation Steps

1. Move config reads into helper functions.
   - `should_store_memories() -> env_flag("ASSISTANT_STORE_MEMORIES", True)`
   - `should_use_memory_context() -> env_flag("ASSISTANT_USE_MEMORY_CONTEXT", True)`
   - This makes tests and runtime env changes predictable.
2. Keep assistant route contract unchanged.
   - Continue using `local-user`.
   - Call new RAG-backed `build_context()` before `assistant_service.complete()`.
   - If retrieval raises unexpectedly, log and continue with no context.
3. Add memory storage gate.
   - Do not persist pure questions/recall requests such as `ai nợ tao tiền?`, `Minh nợ bao nhiêu?`, `lần cuối gặp Minh khi nào?`.
   - Start with deterministic heuristics. Do not add another LLM call in the hot path.
   - Still store factual updates like `Minh nợ tao 60k`, `mai gặp Minh`.
4. Strengthen prompt wording.
   - Keep existing personality behavior.
   - Add instruction: use memory context only when relevant; do not invent facts outside context.
   - Avoid duplicating the context block when personality prompt is active.
5. Update tests.
   - Assistant route passes RAG context when enabled.
   - Route falls back when retrieval fails.
   - Recall question skips background storage.

## Todo List

- [x] Replace import-time flags with helper functions.
- [x] Wire retrieval fallback behavior.
- [x] Add storage gate for recall queries.
- [x] Update prompt tests.

## Success Criteria

- [x] Route tests prove memory context reaches `assistant_service.complete()`.
- [x] Route tests prove no context means `memory_context is None`.
- [x] Recall queries are not saved as memories.
- [x] Assistant audio response behavior remains unchanged.

## Risk Assessment

- Over-simple query detector may skip useful memories. Mitigation: only skip obvious interrogative recall queries; store ambiguous statements.
- Retrieval failure could break voice path. Mitigation: catch/log retrieval errors and continue.
- Prompt changes could affect tone. Mitigation: keep personality prompt structure and add only memory-use guardrail.

## Security Considerations

Do not expose memory context in HTTP response. Avoid logging context by default.

## Next Steps

Run full backend verification and update docs.
