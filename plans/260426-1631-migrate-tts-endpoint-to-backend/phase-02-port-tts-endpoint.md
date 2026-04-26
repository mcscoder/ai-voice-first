# Port TTS Endpoint

## Context Links

- [Plan](./plan.md)
- [TTS Source](/home/mcs/Workspaces/ai-voice-first/TTS-test/main.py)
- [TTS Endpoint Tests](/home/mcs/Workspaces/ai-voice-first/TTS-test/tests/test-tts-endpoint.py)
- [TTS Synthesis Tests](/home/mcs/Workspaces/ai-voice-first/TTS-test/tests/test-synthesize-speech.py)
- [Backend Package](/home/mcs/Workspaces/ai-voice-first/backend/pyproject.toml)

## Overview

Priority: P1. Status: Completed.

Move the working Edge TTS behavior into backend as a dedicated service and router. Preserve source behavior unless intentionally documented.

## Key Insights

- Source endpoint uses `edge_tts.Communicate(...).stream()`.
- It collects only `audio` chunks.
- Validation is Pydantic-based and rejects bad input with 422.
- Source intentionally lets synthesis errors become FastAPI default 500.

## Requirements

- `POST /tts` accepts JSON: `{"text": "...", "language": "vi|en"}`.
- Default `language` is `vi`.
- Voices:
  - `vi`: `vi-VN-HoaiMyNeural`
  - `en`: `en-US-AriaNeural`
- Trim text before synthesis.
- Reject empty text.
- Reject text longer than 5000 chars after trim.
- Timeout synthesis after 30 seconds.
- Return `audio/mpeg` bytes.
- Return `Content-Disposition: attachment; filename="speech.mp3"`.
- Document binary response schema in OpenAPI.

## Architecture

Target shape:

```text
backend/
├── text_to_speech_service.py # Edge TTS stream collection
└── text_to_speech_routes.py  # request model + /tts route
```

Pseudocode:

```python
audio = await synthesize_speech(request.text, SUPPORTED_LANGUAGES[request.language])
return Response(audio, media_type="audio/mpeg", headers={...})
```

## Related Code Files

- Modify: `/home/mcs/Workspaces/ai-voice-first/backend/pyproject.toml`
- Modify: `/home/mcs/Workspaces/ai-voice-first/backend/uv.lock`
- Modify: `/home/mcs/Workspaces/ai-voice-first/backend/main.py`
- Create: `/home/mcs/Workspaces/ai-voice-first/backend/text_to_speech_service.py`
- Create: `/home/mcs/Workspaces/ai-voice-first/backend/text_to_speech_routes.py`

## Implementation Steps

1. Add `edge-tts` to backend dependencies with `uv add edge-tts`.
2. Copy source constants into TTS modules.
3. Copy `TextToSpeechRequest` validation behavior.
4. Copy `synthesize_speech` behavior.
5. Add `APIRouter` with `POST /tts`.
6. Register TTS router in `main.py`.
7. Keep upstream failure behavior unless product decision says otherwise.

## Todo List

- [x] Add `edge-tts` dependency.
- [x] Create TTS service module.
- [x] Create TTS route module.
- [x] Register route in backend app.
- [x] Confirm OpenAPI shows binary `audio/mpeg`.

## Success Criteria

- Valid Vietnamese request returns MP3 bytes.
- Valid English request selects English voice.
- Invalid language returns 422.
- Whitespace and oversized text return 422.
- Timeout and no-audio stream still raise server errors by default.

## Risk Assessment

- Risk: Edge TTS is remote and can fail or throttle. Mitigation: keep timeout; document remote dependency.
- Risk: adding TTS increases public abuse surface. Mitigation: docs warn auth/rate limit before public exposure.
- Risk: dependency changes affect Python 3.11 compatibility. Mitigation: verify `uv sync` and tests in backend.

## Security Considerations

- Submitted text leaves server for Edge TTS. Document privacy impact.
- Do not log submitted text.
- Add auth/rate limiting before exposing publicly; out of scope for migration.

## Next Steps

After route is wired, add backend tests copied and adapted from `TTS-test`.
