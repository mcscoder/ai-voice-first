# Backend TTS Migration

**Date**: 2026-04-26 16:57
**Severity**: Medium
**Component**: `backend/main.py`, TTS route/service, backend docs
**Status**: Resolved

## What Happened

Moved `POST /tts` out of `TTS-test` and into the FastAPI backend. While doing that, `backend/main.py` was split into config, transcription, and TTS modules, and the backend README was updated with `/tts` usage, validation rules, and public-exposure warnings.

## The Brutal Truth

`backend/main.py` had already grown into a monolith, and leaving TTS in the test app would have kept the real backend incomplete. This was basic cleanup that should not have dragged on this long. The work landed cleanly, but the endpoint still needs hardening before anyone exposes it publicly.

## Technical Details

- Added Edge TTS synthesis with `vi` as the default voice and `en` as the alternate language.
- Kept the existing `POST /transcribe` path intact while extracting backend wiring into smaller modules.
- Added dependency updates for `edge-tts`, `pytest`, and `httpx`.
- Added FastAPI tests for route registration, TTS validation, OpenAPI binary response schema, synthesis failure paths, transcription regression behavior, and startup lifespan handling.
- Validation passed with `uv run python -m compileall .` and `uv run pytest` in `backend`, covering 20 tests.

## What We Tried

- Split `main.py` instead of adding more logic to the monolith.
- Kept TTS timeout and upstream failures on default FastAPI error behavior for now.
- Monkeypatched Edge TTS and Whisper in tests so local validation stayed deterministic.
- Added `load_dotenv()` in `transcription_service.py` so direct imports still respect Whisper env settings.

## Root Cause Analysis

The real problem was architectural drift. TTS lived in the wrong app, `main.py` had become too dense, and the backend had no proper test coverage before the migration. That combination made the endpoint harder to trust than it should have been.

## Lessons Learned

- Move runtime endpoints into the real backend early instead of letting a test app become the source of truth.
- Keep app wiring thin and split service logic before the file grows past the point of easy review.
- Do not rely on live external calls in tests when monkeypatching gives stable coverage.
- Treat public TTS exposure as a security and abuse-risk problem, not just a routing problem.

## Next Steps

- Add auth, rate limiting, concurrency caps, and request body limits before public `/tts` exposure.
- Completed: mapped TTS upstream timeout and failure cases to explicit `504` and `502` responses.
