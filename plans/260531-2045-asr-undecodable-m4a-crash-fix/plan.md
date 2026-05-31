---
title: "ASR Undecodable M4A Crash Fix"
description: "Stop undecodable Android .m4a uploads from killing the ASR worker and turning voice assistant requests into EOF-driven 500s."
status: complete
priority: P1
effort: 3h
branch: faster-whisper
tags: [backend, asr, bugfix, voice, assistant]
created: 2026-05-31
---

# ASR Undecodable M4A Crash Fix

## Overview

Android uploads reach `backend/assistant_routes.py:84-105`, which writes a temp file and awaits `transcription_service.transcribe()`. Inside the ASR worker, `_LocalTranscriptionModel.transcribe()` calls `sf.read()` and `sf.info()` with no decode guard at `backend/transcription_service.py:87-103`, and `_run_asr_worker()` sends only success payloads at `backend/transcription_service.py:180-197`. When libsndfile rejects the container, the child dies, the parent `recv()` at `backend/transcription_service.py:173-177` surfaces `EOFError`, and the request falls through as a 500 instead of a typed transcription error even though both routes already map `AudioTranscriptionError` to 400 and `BackendTranscriptionError` to 500 in `backend/assistant_routes.py:157-160` and `backend/transcription_routes.py:50-53`.

Related scout notes: [reports/scout-report.md](./reports/scout-report.md)

## Locked Decision

- Fix the crash by decoding Android `.m4a`/AAC uploads through a bounded `ffmpeg` fallback when `soundfile` cannot read the file.
- Keep the ASR worker alive for expected decode failures by returning structured error frames; reset the worker on parent-side timeout or disconnect to avoid stale pipe responses.
- Recommended HTTP status: `400` for bad or too-large uploaded audio and `500` for backend decode misconfiguration such as missing `ffmpeg`.

## Phases

| Phase | Name | Status |
|-------|------|--------|
| 1 | [Scout And Failure Contract](./phase-01-scout-and-failure-contract.md) | Complete |
| 2 | [Transcription Service Hardening](./phase-02-transcription-service-hardening.md) | Complete |
| 3 | [Regression Tests For Service And Routes](./phase-03-regression-tests-for-service-and-routes.md) | Complete |
| 4 | [Verification And Docs Review](./phase-04-verification-and-docs-review.md) | Complete |

## Dependencies

- `ffmpeg` is now a host runtime requirement for compressed mobile uploads.
- Keep ASR startup and shutdown flow unchanged in `backend/main.py:18-27`.
- Run phases sequentially. File ownership is isolated: Phase 2 owns `backend/transcription_service.py`; Phase 3 owns tests; Phase 4 owns verification/docs only.

## Success Criteria

- `/v1/voice/assistant` and `/transcribe` decode Android `.m4a`/AAC uploads on hosts with `ffmpeg`.
- `/v1/voice/assistant` and `/transcribe` return typed errors instead of surfacing raw worker EOFs.
- A bad `.m4a` does not terminate the ASR worker for the current process job loop, or the parent converts any unexpected worker exit into a typed backend error and clears stale state.
- Existing happy-path and empty-input behavior covered in `backend/tests/test_app_routes.py:23-67` and `backend/tests/test_app_routes.py:141-177,331-363` stays intact.
- `cd /home/mcs/Workspaces/ai-voice-first/backend && uv run python -m compileall . && uv run pytest tests/test_app_routes.py tests/test_transcription_service.py -q` passes.

## Test Matrix

- Unit/service: ffmpeg fallback decodes real generated `.m4a`; worker returns structured audio/backend errors without dying; parent raises the matching exception class.
- Integration: `/transcribe` and `/v1/voice/assistant` map audio decode failures to `400` and backend decode misconfiguration to `500`.
- Regression: a decode failure is followed by a valid request path in the same worker lifecycle test.
- Live/e2e: no new live test required; existing optional voice endpoint smoke tests remain unchanged.

## Rollback

- Revert `backend/transcription_service.py` only if the new worker envelope or cleanup path causes broader regressions.
- Remove new regression tests only with the runtime rollback, never alone.
- Docs update, if any, rolls back independently with no data migration.

## Docs Impact

Minor. `backend/README.md` and `backend/docs/GPU_SETUP.md` document the new `ffmpeg` runtime requirement and decode error contract.

## Unresolved Questions

None.
