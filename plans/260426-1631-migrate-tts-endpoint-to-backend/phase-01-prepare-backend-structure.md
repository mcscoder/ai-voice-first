# Prepare Backend Structure

## Context Links

- [Plan](./plan.md)
- [Backend Main](/home/mcs/Workspaces/ai-voice-first/backend/main.py)
- [Backend README](/home/mcs/Workspaces/ai-voice-first/backend/README.md)
- [TTS Source](/home/mcs/Workspaces/ai-voice-first/TTS-test/main.py)

## Overview

Priority: P1. Status: Completed.

Split the existing backend into importable modules before adding TTS. Current `backend/main.py` is 256 lines; adding TTS directly would violate file-size guidance and make future routing harder.

## Key Insights

- Existing app combines config, enums, service, route, and process entrypoint.
- `service = TranscriptionService()` is global and used by app lifespan.
- Refactor must preserve `uv run python main.py` and `main:app`.

## Requirements

- Keep API behavior for `POST /transcribe`.
- Keep `.env` loading.
- Keep `ASR_LOAD_ON_STARTUP` behavior.
- Do not rename route paths.
- Keep implementation simple; no framework rewrite.

## Architecture

Target shape:

```text
backend/
├── main.py                  # app factory/wiring + uvicorn entrypoint
├── config.py                # env helpers
├── transcription_service.py # ASR service + errors
└── transcription_routes.py  # /transcribe route
```

`main.py` owns app creation and lifespan. `transcription_routes.py` owns FastAPI router. `transcription_service.py` owns model lifecycle and transcription logic.

## Related Code Files

- Modify: `/home/mcs/Workspaces/ai-voice-first/backend/main.py`
- Create: `/home/mcs/Workspaces/ai-voice-first/backend/config.py`
- Create: `/home/mcs/Workspaces/ai-voice-first/backend/transcription_service.py`
- Create: `/home/mcs/Workspaces/ai-voice-first/backend/transcription_routes.py`

## Implementation Steps

1. Move `env_flag` into `config.py`.
2. Move `AudioTranscriptionError`, `BackendTranscriptionError`, `LanguageOption`, and `TranscriptionService` into `transcription_service.py`.
3. Move `transcribe_audio` route into `transcription_routes.py`.
4. Export a router from `transcription_routes.py`.
5. Keep one shared `TranscriptionService` instance that `main.py` can load during lifespan.
6. Register the router in `main.py`.
7. Verify imports work from backend root.

## Todo List

- [x] Extract config helper.
- [x] Extract transcription service.
- [x] Extract transcription route.
- [x] Shrink `main.py` to app wiring.
- [x] Preserve startup model loading.

## Success Criteria

- `POST /transcribe` still exists in OpenAPI.
- `main.py` remains executable.
- `main.py` under 200 lines.
- Compile command passes after refactor.

## Risk Assessment

- Risk: duplicate service instances load ASR model twice. Mitigation: centralize one instance.
- Risk: route import cycles. Mitigation: route module imports service, main imports router only.

## Security Considerations

- Preserve temp file cleanup.
- Preserve empty upload rejection.
- Do not log uploaded file contents.

## Next Steps

After structure is stable, add TTS as separate service and router.
