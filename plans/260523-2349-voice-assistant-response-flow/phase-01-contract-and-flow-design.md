---
phase: 1
title: "Contract And Flow Design"
status: complete
priority: P1
effort: 2h
dependencies: []
---

# Phase 1: Contract And Flow Design

## Overview

Define the exact request/response contract for the assistant flow before touching runtime
code. This phase decides what the backend receives from Flutter, what the backend returns,
and what data stays server-only.

## Requirements

- Functional:
  - Keep the current voice capture UX shape: press to record, press to stop, then wait for a response.
  - Preserve language selection for transcription hints if needed.
  - Return assistant reply text to the client.
  - Keep transcript text backend-only unless explicitly needed for debug logs.
- Non-functional:
  - Flutter must not know the assistant provider URL or API key.
  - Sensitive prompt text and provider credentials stay in backend config.
  - Contract must be simple enough to test without live network access.

## Architecture

Proposed flow:

```text
Flutter voice screen
  -> record audio locally
  -> upload audio file to backend
Backend assistant endpoint
  -> transcribe audio
  -> build prompt
  -> call local chat completions API
  -> return assistant reply
Flutter
  -> render reply state
```

The backend should remain the only place where transcription text and system prompts are
visible together. The Flutter app should receive only the reply payload it needs to render.

## Related Code Files

- Read:
  - `app/lib/features/voice/presentation/voice_capture_cubit.dart`
  - `app/lib/features/voice/presentation/voice_capture_state.dart`
  - `app/lib/features/voice/presentation/voice_screen.dart`
  - `app/lib/features/voice/data/transcription_api.dart`
  - `app/lib/core/network/api.dart`
  - `app/lib/core/network/api_path.dart`
  - `backend/main.py`
  - `backend/transcription_routes.py`
  - `backend/transcription_service.py`
  - `backend/README.md`
- Modify later:
  - `app/lib/features/voice/*`
  - `app/lib/core/network/api_path.dart`
  - `backend/*`

## Implementation Steps

1. Use `POST /v1/voice/assistant` as the single voice-to-assistant endpoint.
2. Accept multipart `file` plus optional form `language` so Flutter keeps using the existing audio upload path.
3. Return only `reply` and `language` to the client.
4. Make the assistant reply language follow the selected voice language unless backend prompt logic says otherwise.
5. Set the request timeout budget to 45 seconds end-to-end.
6. Lock the Flutter state model around `idle`, `recording`, `uploading`, `processing`, `success`, and `failure`.
7. Write the backend-only config contract for provider URL, token, model, and system prompt.

## Todo List

- [x] Define request payload.
- [x] Define response payload.
- [x] Define env config names.
- [x] Define timeout budget.
- [x] Define UI state model.

## Success Criteria

- Contract is explicit and narrow.
- No client-side assistant provider dependency is left in the design.
- No transcript text is exposed in the client-facing response unless there is a strong reason.

## Risk Assessment

- If the contract is vague, the Flutter refactor will drift and leak backend details.
- If the timeout is too short, users will see random failures on valid voice requests.

## Security Considerations

- Do not put provider keys, prompts, or backend-only prompts in Flutter.
- Do not expose raw transcript text unless it is required and justified.

## Next Steps

Proceed to backend orchestration once the contract is fixed.
