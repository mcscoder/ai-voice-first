---
phase: 2
title: "Transcription Service Hardening"
status: complete
priority: P1
effort: "1h"
dependencies: [1]
---

# Phase 2: Transcription Service Hardening

## Context Links

- Decode call site: `backend/transcription_service.py:87-103`
- Parent IPC path: `backend/transcription_service.py:157-177`
- Worker loop: `backend/transcription_service.py:180-197`
- Startup lifecycle to preserve: `backend/main.py:18-27`

## Overview

Fix the root cause in the shared ASR service by converting decode failures into typed audio errors and preventing one bad upload from taking down the worker loop.

## Key Insights

- Route changes are probably unnecessary because both routes already map `AudioTranscriptionError` and `BackendTranscriptionError`.
- The worker currently has success-only messaging. A small result-or-error envelope is enough; no protocol redesign needed.
- Parent-side EOF handling is still needed as a last-resort guard for unexpected worker exits.

## Requirements

- Functional: undecodable audio returns `AudioTranscriptionError`; unexpected worker exits return `BackendTranscriptionError`.
- Non-functional: no new dependencies, no route contract changes, no startup/lifecycle changes.

## Architecture

Use a small pipe message envelope:
- success: `{"result": ...}`
- client audio error: `{"error_type": "audio", "detail": ...}`
- internal failure: `{"error_type": "backend", "detail": ...}`

Parent side reads one envelope and re-raises the matching local exception class. Worker side catches per-job exceptions so the process keeps serving later requests.

## Related Code Files

- Modify: `backend/transcription_service.py`
- Read only: `backend/assistant_routes.py`, `backend/transcription_routes.py`, `backend/main.py`
- Do not touch: Flutter files, TTS files, dependency manifests

## Implementation Steps

1. In `_LocalTranscriptionModel.transcribe()`, catch known unreadable-audio failures around `soundfile.read/info` and raise `AudioTranscriptionError` with a stable app-level message instead of leaking libsndfile text.
2. In `_run_asr_worker()`, wrap each `RUN` job so `AudioTranscriptionError` becomes an audio error envelope and unexpected exceptions become a backend error envelope instead of terminating the child.
3. In `TranscriptionService.transcribe()`, inspect the received envelope and raise `AudioTranscriptionError` or `BackendTranscriptionError` locally.
4. Add a last-resort guard around pipe send/recv (`EOFError`, broken pipe, connection reset) that clears stale worker state and raises `BackendTranscriptionError`.
5. Leave `load_model()` and `shutdown_model()` behavior intact unless the EOF cleanup path requires a minimal state reset.

## Todo List

- [ ] Add stable app-level message for unreadable audio.
- [ ] Add worker per-job exception envelope.
- [ ] Add parent envelope parsing.
- [ ] Add parent fallback for unexpected worker exit.
- [ ] Keep startup lifecycle unchanged.

## Success Criteria

- [ ] A decode failure no longer exits the worker loop as an unhandled exception.
- [ ] Parent callers receive typed local exceptions, not raw EOFs.
- [ ] Valid audio requests still use the same success path and payload shape.

## Risk Assessment

- Risk: over-catching model/runtime bugs as `AudioTranscriptionError`. Likelihood medium, impact high.
  Mitigation: catch only known decode/input failures as audio errors; everything else stays backend.
- Risk: leaving stale pipe/process references after EOF. Likelihood medium, impact medium.
  Mitigation: clear local worker state on unexpected transport failure before raising.

## Security Considerations

Do not echo raw decoder/library internals back to clients. Use a stable, low-information message.

## Rollback

Revert `backend/transcription_service.py` only. No schema, config, or API migration is involved.

## Next Steps

Lock the new behavior with offline tests in Phase 3.
