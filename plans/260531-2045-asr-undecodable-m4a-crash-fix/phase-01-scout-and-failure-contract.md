---
phase: 1
title: "Scout And Failure Contract"
status: complete
priority: P1
effort: "20m"
dependencies: []
---

# Phase 1: Scout And Failure Contract

## Context Links

- Scout report: [reports/scout-report.md](./reports/scout-report.md)
- Assistant request path: `backend/assistant_routes.py:84-105`
- ASR IPC path: `backend/transcription_service.py:157-197`
- Current route error mapping: `backend/assistant_routes.py:157-160`, `backend/transcription_routes.py:50-53`
- Existing route tests: `backend/tests/test_app_routes.py:23-67`, `backend/tests/test_app_routes.py:141-177`, `backend/tests/test_app_routes.py:331-363`

## Overview

Lock the exact bug boundary before implementation: unreadable uploaded audio currently kills the ASR worker instead of returning a typed API error. This phase stays read-only and defines the contract the later fix must satisfy.

## Key Insights

- The crash originates in shared transcription runtime code, not the route layer.
- The route layer already has the right exception split; the missing piece is getting typed exceptions back from the worker.
- The smallest compatible behavior change is `400` for bad uploaded audio, not a new `415` branch or format-conversion feature.

## Requirements

- Functional: identify the exact request path, worker path, and status-code target.
- Non-functional: no runtime code changes, no dependency changes, no speculative format support work.

## Architecture

Current flow is upload -> temp file -> ASR worker -> transcript -> assistant/TTS. The fix point is the ASR worker boundary, because both HTTP routes already consume typed transcription exceptions.

## Related Code Files

- Modify: none
- Read only: `backend/assistant_routes.py`, `backend/transcription_service.py`, `backend/transcription_routes.py`, `backend/tests/test_app_routes.py`, `backend/README.md`

## Implementation Steps

1. Confirm the upload path and error mapping from source, not assumption.
2. Lock `400` as the recommended status for unreadable uploaded audio because it aligns with existing client-input validation at `backend/README.md:101-110`.
3. Record the missing worker error envelope and parent EOF translation as the concrete root cause.
4. Hand off exact file ownership to later phases so no two phases need the same file.

## Todo List

- [ ] Confirm current failure path from route to worker.
- [ ] Confirm current HTTP exception mapping.
- [ ] Confirm existing tests do not cover decode failure.
- [ ] Freeze minimal scope: no transcoding, no new deps, no client changes.

## Success Criteria

- [ ] Root cause is written as a source-cited statement, not a guess.
- [ ] Status-code recommendation is explicit.
- [ ] Later phases have isolated file ownership.

## Risk Assessment

- Risk: silently broadening scope into audio-format support. Likelihood medium, impact high.
  Mitigation: keep this plan on error translation only.
- Risk: choosing a new HTTP status that forces client-contract drift. Likelihood low, impact medium.
  Mitigation: stick with existing 400/500 route pattern.

## Security Considerations

No security change. This is error-handling only; no auth, storage, or network surface changes.

## Next Steps

Implement the service-level fix in Phase 2.
