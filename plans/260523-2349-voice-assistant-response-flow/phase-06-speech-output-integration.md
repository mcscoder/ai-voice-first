---
phase: 6
title: "Speech Output Integration"
status: complete
priority: P1
effort: 6h
dependencies: [2, 3]
---

# Phase 6: Speech Output Integration

## Overview

Extend the assistant flow so the backend returns synthesized speech instead of reply text.
Flutter should upload audio, receive MP3 bytes, and play them locally. The backend remains the
only place where transcription, assistant prompting, and speech generation happen.

## Requirements

- Functional:
  - Reuse the existing assistant route.
  - Transcribe audio server-side.
  - Call the assistant chat completions API server-side.
  - Synthesize the assistant reply with the existing TTS implementation.
  - Return audio bytes to Flutter.
  - Play the returned audio in the app.
- Non-functional:
  - Keep assistant/provider secrets backend-only.
  - Avoid exposing the transcript text to Flutter.
  - Keep the client request shape small.
  - Add deterministic tests for both backend and Flutter.

## Architecture

Implemented flow:

```text
Flutter record -> upload audio -> backend transcribe -> backend assistant reply -> backend TTS
-> Flutter audio playback
```

The backend should remain the only caller of the assistant provider and the TTS service.
Flutter should only deal with audio upload and playback.

## Related Code Files

- Modify:
  - `backend/assistant_routes.py`
  - `backend/text_to_speech_service.py`
  - `backend/text_to_speech_routes.py`
  - `backend/README.md`
  - `backend/tests/test_app_routes.py`
  - `backend/tests/test_text_to_speech_endpoint.py` if route behavior changes
  - `app/pubspec.yaml`
  - `app/lib/features/voice/data/transcription_api.dart`
  - `app/lib/features/voice/presentation/voice_capture_cubit.dart`
  - `app/lib/features/voice/presentation/voice_capture_state.dart`
  - `app/lib/features/voice/presentation/voice_screen.dart`
  - `app/test/transcription_api_test.dart`
  - `app/test/voice_capture_cubit_test.dart`
  - `app/test/widget_test.dart`

## Implementation Steps

1. Make the assistant backend route synthesize speech after it gets the reply text.
2. Return audio bytes from `POST /v1/voice/assistant`.
3. Keep the TTS voice selection aligned with the assistant language.
4. Add a Flutter audio player dependency and wire playback into the voice flow.
5. Update the cubit and screen states so the user sees a speaking state instead of text-only output.
6. Update tests to cover the binary response path and playback integration.

## Todo List

- [x] Wire backend assistant route to TTS.
- [x] Move shared TTS voice mapping to a reusable backend location.
- [x] Add Flutter audio playback dependency.
- [x] Refactor Flutter voice API to consume audio bytes.
- [x] Refactor cubit and screen for speaking state.
- [x] Update tests and smoke checks.

## Success Criteria

- Voice input results in audio playback from the backend response.
- No assistant reply text is required in the Flutter UI path.
- The backend still owns transcription, prompt building, assistant calls, and TTS.
- Backend and Flutter tests pass.

## Risk Assessment

- Response size increases because audio is returned inline.
- Playback failures can be platform specific if the audio player dependency is wrong.
- Any accidental text leak into the client violates the privacy boundary.

## Security Considerations

- Keep all provider URLs, keys, and prompt text on the backend.
- Do not persist the generated audio unless there is a product reason.
- Keep temp-file cleanup and request timeout handling in place.

## Next Steps

Implement the backend response change first, then wire the Flutter audio playback path.
