# Add Tests And Validation

## Context Links

- [Plan](./plan.md)
- [Source Endpoint Tests](/home/mcs/Workspaces/ai-voice-first/TTS-test/tests/test-tts-endpoint.py)
- [Source Synthesis Tests](/home/mcs/Workspaces/ai-voice-first/TTS-test/tests/test-synthesize-speech.py)
- [Source Test Fixtures](/home/mcs/Workspaces/ai-voice-first/TTS-test/tests/conftest.py)

## Overview

Priority: P1. Status: Completed.

Add a backend test suite that verifies migrated TTS behavior without calling the remote Edge TTS service.

## Key Insights

- Source tests use `httpx.ASGITransport`.
- Source tests stub `synthesize_speech`.
- Backend has no tests currently.
- Lifespan may load ASR model by default; tests should disable startup model loading.

## Requirements

- Use real FastAPI app tests, not endpoint-only simulation.
- Do not call remote Edge TTS in tests.
- Do not load ASR model in tests.
- Preserve source behavior assertions.
- Include at least one regression check for `/transcribe` route registration.

## Architecture

Target shape:

```text
backend/tests/
├── conftest.py
├── test_text_to_speech_endpoint.py
├── test_text_to_speech_service.py
└── test_app_routes.py
```

Set `ASR_LOAD_ON_STARTUP=false` before importing app or create app with test-safe config if implementation supports it.

## Related Code Files

- Modify: `/home/mcs/Workspaces/ai-voice-first/backend/pyproject.toml`
- Modify: `/home/mcs/Workspaces/ai-voice-first/backend/uv.lock`
- Create: `/home/mcs/Workspaces/ai-voice-first/backend/tests/conftest.py`
- Create: `/home/mcs/Workspaces/ai-voice-first/backend/tests/test_text_to_speech_endpoint.py`
- Create: `/home/mcs/Workspaces/ai-voice-first/backend/tests/test_text_to_speech_service.py`
- Create: `/home/mcs/Workspaces/ai-voice-first/backend/tests/test_app_routes.py`

## Implementation Steps

1. Add dev dependencies: `uv add --dev pytest httpx`.
2. Add pytest config with `pythonpath = ["."]` if needed.
3. Create async HTTP client fixtures.
4. Port source endpoint tests and update monkeypatch targets.
5. Port synthesis timeout and no-audio tests.
6. Add route registration test for `/transcribe` and `/tts` in OpenAPI.
7. Run compile and tests from `backend`.

## Todo List

- [x] Add test dependencies.
- [x] Add ASGI client fixtures.
- [x] Port TTS endpoint tests.
- [x] Port TTS service tests.
- [x] Add app route regression test.
- [x] Run compileall.
- [x] Run pytest.

## Success Criteria

- `uv run python -m compileall .` passes from `backend`.
- `uv run pytest` passes from `backend`.
- Tests do not require network.
- Tests do not require ASR model download/load.
- Validation failures return expected 422 responses.

## Risk Assessment

- Risk: importing `main.app` triggers ASR model load. Mitigation: disable via environment before import or expose app factory.
- Risk: async test dependency mismatch. Mitigation: match source `pytest` + `httpx` pattern.

## Security Considerations

- Tests must not use real confidential text.
- Tests must not make network calls to Edge TTS.

## Next Steps

After tests pass, update backend docs with `/tts` usage and operational caveats.
