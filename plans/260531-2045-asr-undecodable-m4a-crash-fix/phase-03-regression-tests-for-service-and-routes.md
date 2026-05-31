---
phase: 3
title: "Regression Tests For Service And Routes"
status: complete
priority: P1
effort: "1h"
dependencies: [2]
---

# Phase 3: Regression Tests For Service And Routes

## Context Links

- Existing route coverage: `backend/tests/test_app_routes.py:23-67`, `backend/tests/test_app_routes.py:141-177`, `backend/tests/test_app_routes.py:331-363`
- Service code under test: `backend/transcription_service.py:87-197`
- Route mappings expected to stay unchanged: `backend/assistant_routes.py:157-160`, `backend/transcription_routes.py:50-53`

## Overview

Add deterministic, offline regressions that prove the worker no longer crashes on undecodable audio and that both HTTP routes return the expected status code.

## Requirements

- Functional: service-level regression for worker error handling and route-level regressions for 400 mapping.
- Non-functional: no live ASR model, no GPU, no ffmpeg, no network.

## Architecture

Test in two layers:
- service test: direct ASR worker/service behavior with fakes so the multiprocessing boundary is exercised without loading the real model
- route tests: monkeypatch `transcription_service.transcribe` to raise `AudioTranscriptionError` and assert HTTP 400 responses

## Related Code Files

- Create: `backend/tests/test_transcription_service.py`
- Modify: `backend/tests/test_app_routes.py`
- Read only: `backend/transcription_service.py`, `backend/assistant_routes.py`, `backend/transcription_routes.py`

## Implementation Steps

1. Add a service regression that simulates one decode failure followed by one valid result and proves the worker/process path stays usable.
2. Add `/v1/voice/assistant` route regression: monkeypatch `assistant_routes.transcription_service.transcribe` to raise `AudioTranscriptionError` and assert 400 plus stable detail.
3. Add `/transcribe` route regression: monkeypatch `transcription_routes.transcription_service.transcribe` to raise `AudioTranscriptionError` and assert 400 plus the same detail.
4. Keep assertions on app-level error detail, not raw `soundfile` exception text.

## Todo List

- [ ] Add service worker regression test.
- [ ] Add `/v1/voice/assistant` decode-failure route test.
- [ ] Add `/transcribe` decode-failure route test.
- [ ] Keep tests fully offline and deterministic.

## Success Criteria

- [ ] Tests fail before Phase 2 or clearly encode the missing behavior.
- [ ] Tests pass after Phase 2 without requiring real audio decoding.
- [ ] Existing success and empty-input tests stay unchanged.

## Risk Assessment

- Risk: multiprocessing tests become platform-fragile. Likelihood medium, impact medium.
  Mitigation: patch module symbols before worker start and keep assertions minimal; if CI start method blocks that, fall back to testing parent envelope parsing directly and keep route regressions.
- Risk: exact-message assertions become brittle. Likelihood medium, impact low.
  Mitigation: assert the stable app-level message chosen in Phase 2, not library wording.

## Security Considerations

Use synthetic bytes and fake exceptions only. No real user audio in fixtures.

## Rollback

Remove new tests only together with the runtime rollback from Phase 2.

## Next Steps

Run compile/test verification and update docs only if the new error message becomes part of the supported contract.
