# Voice Assistant Response Flow

**Date**: 2026-05-23
**Severity**: Medium
**Component**: `backend/assistant_routes.py`, `backend/assistant_service.py`, `app/lib/features/voice/*`
**Status**: Resolved

## What Happened

Replaced the transcript-only voice flow with a backend-orchestrated assistant flow. Flutter
now records audio, uploads it to `POST /v1/voice/assistant`, and renders the assistant reply.
The backend transcribes audio, assembles the prompt, and calls the local chat completions API
with the API key and model kept server-side.

## Technical Details

- Added backend assistant orchestration around Whisper transcription and the local OpenAI-compatible chat completions endpoint.
- Kept `/transcribe` and `/tts` stable for compatibility.
- Added backend env config for assistant base URL, API key, model, provider timeout, and system prompt.
- Refactored Flutter voice state from transcript text to assistant reply text with `idle`, `recording`, `uploading`, `processing`, `success`, and `failure` states.
- Increased client-side timeouts to 45 seconds to match the new end-to-end request budget.
- Updated app and backend docs so the repo no longer describes the product as transcript-only.

## Validation

- `dart format` on modified Flutter files.
- `flutter test` passed.
- `flutter analyze` passed.
- `uv run python -m compileall .` passed in `backend`.
- `uv run pytest` passed in `backend`: 27 tests.

## Root Cause Analysis

The old voice flow stopped at transcription, which made the app feel like a speech-to-text demo.
The real product requirement was assistant replies, so the backend needed to own the entire
transcription + prompt + completion chain.

## Lessons Learned

- Keep the client thin when the backend already owns the sensitive logic.
- Lock the API contract before refactoring the UI state machine.
- Update docs immediately after a product flow changes, or the repo starts telling the wrong story.

