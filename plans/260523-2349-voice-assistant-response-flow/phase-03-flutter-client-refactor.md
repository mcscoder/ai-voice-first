---
phase: 3
title: "Flutter Client Refactor"
status: complete
priority: P1
effort: 4h
dependencies: [1, 2]
---

# Phase 3: Flutter Client Refactor

## Overview

Refactor the Flutter voice feature so it no longer renders transcript output. The client
still records audio and handles mic permission, but it now sends the audio to the backend
and shows the assistant reply that comes back.

## Requirements

- Functional:
  - Keep microphone permission handling and recording local.
  - Upload recorded audio to backend only.
  - Render assistant reply instead of transcript text.
  - Preserve a simple busy/failure state for the UI.
- Non-functional:
  - Do not call the assistant provider directly from Flutter.
  - Keep the client request shape narrow and backend-driven.
  - Keep the feature small enough to maintain without more monolith growth.

## Architecture

Implemented client shape:

```text
app/lib/features/voice/
├── data/
│   └── audio_recorder_service.dart
├── presentation/
│   ├── voice_capture_cubit.dart
│   ├── voice_capture_state.dart
│   └── voice_screen.dart
```

The client should:

1. Record audio locally.
2. Upload audio to backend.
3. Wait for backend reply.
4. Show assistant text in the center of the screen.

The transcript is not a UI artifact anymore. If it is needed for diagnostics, it stays
behind the backend boundary.

## Related Code Files

- Modify:
  - `app/lib/features/voice/data/audio_recorder_service.dart`
  - `app/lib/core/network/api_path.dart`
  - `app/lib/core/network/api.dart` if timeout handling needs tuning
  - `app/lib/core/router/router.dart`
  - `app/lib/core/di/get_it.dart`
  - `app/lib/core/di/get_it.config.dart`
  - `app/lib/app.dart` if app bootstrap needs a timeout or state tweak
- Replace or create:
  - `app/lib/features/voice/data/transcription_api.dart`
  - `app/lib/features/voice/data/transcription_response.dart`
  - `app/lib/features/voice/presentation/voice_capture_cubit.dart`
  - `app/lib/features/voice/presentation/voice_capture_state.dart`
  - `app/lib/features/voice/presentation/voice_screen.dart`
- Possibly create:
  - `app/lib/features/voice/data/voice_assistant_api.dart`
  - `app/lib/features/voice/data/voice_assistant_response.dart`
  - `app/lib/features/voice/presentation/voice_assistant_cubit.dart`
  - `app/lib/features/voice/presentation/voice_assistant_state.dart`
  - `app/lib/features/voice/presentation/voice_assistant_screen.dart`

## Implementation Steps

1. Rename the voice flow state around assistant replies, not transcript text.
2. Swap the API client to the backend assistant endpoint.
3. Keep language selection if it still matters for transcription accuracy.
4. Remove transcript-specific rendering from the screen.
5. Make the screen show assistant response and clear busy states cleanly.
6. Keep dependency injection and routing stable.
7. Keep error messaging simple and user-facing.

## Todo List

- [x] Create assistant API client.
- [x] Create assistant response model.
- [x] Refactor cubit/state to assistant semantics.
- [x] Update screen rendering.
- [x] Update router and DI wiring.

## Success Criteria

- App no longer presents the flow as transcript-only.
- User speaks, backend handles processing, app shows assistant reply.
- Flutter has no direct dependency on assistant provider internals.

## Risk Assessment

- Renaming the voice feature can cause noisy diffs if not done in one pass.
- If the state machine stays transcript-shaped, the UI will still feel wrong.

## Security Considerations

- Do not move prompt logic or secret values into Flutter.
- Keep the client payload minimal and backend-owned.

## Next Steps

Add tests around the new assistant flow and ensure the old transcript contract is gone from the UI.
