---
phase: 2
title: "Backend Assistant Orchestration"
status: complete
priority: P1
effort: 4h
dependencies: [1]
---

# Phase 2: Backend Assistant Orchestration

## Overview

Add the server-side service layer that accepts an uploaded audio file, transcribes it,
builds the assistant prompt, and calls the local chat completions API. This is the core
privacy boundary: the backend owns all sensitive processing.

## Requirements

- Functional:
  - Accept voice input from Flutter.
  - Reuse the existing Whisper transcription service.
  - Call the local assistant chat completions API with backend-managed credentials.
  - Return assistant reply text in a stable response schema.
  - Keep the existing `/transcribe` route intact for compatibility.
- Non-functional:
  - Use backend env for base URL, token, model, and system prompt.
  - Add request timeout and clear error mapping.
  - Avoid logging raw transcript text or secrets.

## Architecture

Implemented backend shape:

```text
backend/
├── assistant_routes.py
├── assistant_service.py
├── config.py
├── main.py
└── transcription_service.py
```

Suggested flow:

1. Route receives audio file and optional language hint.
2. Service writes temp file and uses Whisper transcription.
3. Service builds a backend-only prompt using system prompt + transcript.
4. Client calls the local OpenAI-compatible `/v1/chat/completions` endpoint.
5. Route returns assistant reply text and minimal metadata.

The chat provider URL and token must live in backend `.env`, not in Flutter.
The public backend route should be `POST /v1/voice/assistant`.

## Related Code Files

- Modify:
  - `backend/main.py`
  - `backend/assistant_routes.py`
  - `backend/assistant_service.py`
  - `backend/README.md`
  - `backend/.env.example`
  - `backend/pyproject.toml`
  - `backend/tests/*`

## Implementation Steps

1. Add assistant env config names to backend docs and env examples.
2. Reuse Whisper transcription to turn uploaded audio into text.
3. Build the assistant prompt server-side only.
4. Return a compact response model with reply text and language metadata.
5. Map remote failures to explicit FastAPI errors.
6. Register the new router in `main.py` without breaking existing routes.

## Todo List

- [x] Add backend env config.
- [x] Add assistant HTTP client.
- [x] Add assistant orchestration service.
- [x] Add assistant route.
- [x] Keep transcription route working.
- [x] Document new backend endpoint.

## Success Criteria

- Backend can accept voice input and return an assistant reply.
- Flutter does not call the assistant provider directly.
- Secrets and prompt logic stay in backend env/service code.
- Existing transcription route still works.

## Risk Assessment

- A long combined request may hit timeouts.
- The assistant provider may fail independently of the backend.
- A bad prompt or response schema can break the client quickly if not versioned.

## Security Considerations

- Never log the assistant API key or prompt content.
- Keep temp file cleanup and request-size limits in place.
- Add auth/rate limiting before any public exposure.

## Next Steps

Wire the client to this backend endpoint after the route is stable.
