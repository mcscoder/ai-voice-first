# Voice Assistant Speech Output

**Date**: 2026-05-24
**Severity**: Medium
**Component**: `backend/assistant_routes.py`, `backend/assistant_service.py`, `backend/text_to_speech_service.py`, `app/lib/features/voice/*`
**Status**: Resolved

## What Happened

Extended the assistant voice flow from reply-text output to speech output. Flutter now records
audio, uploads it to `POST /v1/voice/assistant`, receives `audio/mpeg` bytes, and plays the
assistant speech locally. The backend now owns transcription, assistant prompting, and TTS.

## Technical Details

- Reused the existing backend TTS pipeline inside the assistant route.
- Moved shared TTS voice mapping into the backend TTS service module.
- Changed the assistant endpoint response contract from JSON to `audio/mpeg`.
- Added Flutter audio playback via `audioplayers` and made the player lazy so unit tests stay
  pure Dart when they inject a fake playback callback.
- Refactored the voice UI state to add a speaking state and keep the UI disabled while audio
  is playing.
- Updated Flutter localization strings so the screen copy matches an audio-first flow.

## Validation

- `uv run python -m compileall .` passed in `backend`.
- `uv run pytest tests/test_assistant_service.py -q` passed.
- `uv run pytest tests/test_app_routes.py::test_voice_assistant_returns_audio -q` passed.
- `uv run pytest tests/test_app_routes.py::test_voice_assistant_rejects_empty_upload -q` passed.
- `uv run pytest tests/test_app_routes.py::test_voice_assistant_rejects_empty_transcript -q` passed.
- `uv run pytest tests/test_app_routes.py::test_voice_assistant_maps_assistant_timeout_to_gateway_timeout -q` passed.
- `uv run pytest tests/test_text_to_speech_service.py tests/test_text_to_speech_endpoint.py -q` passed: 16 tests.
- Live smoke: `RUN_LIVE_VOICE_ASSISTANT_SMOKE=1` against the real backend returned `audio/mpeg` and passed.
- `flutter test test/transcription_api_test.dart test/voice_capture_cubit_test.dart test/widget_test.dart` passed.
- `flutter analyze` passed.
- `flutter test` passed.

## Root Cause Analysis

The first assistant flow stopped at text because the route contract and Flutter state machine
were still transcript-shaped. The backend already had TTS, so the missing piece was wiring the
assistant reply into speech generation and changing the client to play audio instead of
rendering text.

## Lessons Learned

- Keep the route contract aligned with the actual user experience, not the intermediate data.
- If the client should stay thin, the backend has to own the orchestration end to end.
- Audio player APIs change; verify the current package docs before wiring playback.
