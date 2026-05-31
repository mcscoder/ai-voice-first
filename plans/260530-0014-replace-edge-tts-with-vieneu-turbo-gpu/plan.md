---
title: "Replace Edge TTS With VieNeu Turbo GPU"
description: "Swap backend Edge TTS for local VieNeu Turbo with GPU-first warmup while preserving current HTTP speech contracts."
status: complete
priority: P1
effort: 8h
branch: faster-whisper
tags: [backend, tts, vieneu, gpu, migration]
created: 2026-05-30
---

# Replace Edge TTS With VieNeu Turbo GPU

## Locked Decision

- Preserve the external MP3 contract. VieNeu returns a 24 kHz `numpy.ndarray`, but `/tts` and `/v1/voice/assistant` are currently defined, documented, and tested as `audio/mpeg` with `.mp3` filenames in `backend/text_to_speech_routes.py:37-76`, `backend/assistant_routes.py:50-154`, `backend/README.md:59-127`, `backend/tests/test_text_to_speech_endpoint.py:19-174`, and `backend/tests/test_app_routes.py:103-154`.
- Use direct VieNeu SDK, not an HTTP sidecar. Use explicit `Vieneu(mode="turbo_gpu")` and lock target behavior to `pnnbao-ump/VieNeu-TTS-v2-Turbo`.
- Keep route paths and request shapes unchanged. This avoids breaking the current voice pipeline that later plans already assume exists in `plans/260524-0736-personal-knowledge-brain/plan.md:21-24` and `:38-41`.

## Data Flow

- `/tts`: JSON text -> `TextToSpeechRequest` validation in `backend/text_to_speech_routes.py:22-35` -> TTS worker process -> VieNeu waveform @ 24 kHz -> MP3 encode -> `Response(audio/mpeg, speech.mp3)`.
- `/v1/voice/assistant`: upload -> ASR worker process -> assistant reply -> TTS worker process -> `Response(audio/mpeg, assistant-speech.mp3)` as wired in `backend/assistant_routes.py:80-154`.
- Model lifecycle: app startup starts ASR and TTS worker processes; each process loads its own CUDA model once and handles requests through local process pipes.

## Phases

### Phase 1: Runtime Swap

- Status: complete
- Blockers: none
- Files: `backend/pyproject.toml`, `backend/uv.lock`, `backend/text_to_speech_service.py`, `backend/main.py`, `backend/tests/conftest.py`
- Work:
  1. Remove `edge-tts`, add `vieneu[gpu]`, keep `soundfile`; current deps live in `backend/pyproject.toml:7-17`.
  2. Replace Edge stream/fallback code in `backend/text_to_speech_service.py:10-48` with a shared VieNeu-backed synthesizer that:
     - trims to existing `MAX_TEXT_LENGTH`
     - maps app language (`vi`/`en`) to the minimum VieNeu-compatible input behavior
     - returns MP3 bytes by encoding the 24 kHz waveform in-process
     - keeps no-audio as the only TTS domain exception; runtime failures are not wrapped
  3. Extend startup in `backend/main.py:17-28` with TTS preload so first download/warmup does not burn the 30s/45s request budgets.
  4. Set test env to skip TTS preload by default in `backend/tests/conftest.py:9-13`.
- Failure modes:
  - High x High: `vieneu[gpu]` lock/install conflict with existing GPU stack. Mitigation: fail early at `uv lock`; if extras resolution fails, fall back to plain `vieneu` plus documented host GPU runtime, not a silent provider mix.
  - High x High: first model download/warmup exceeds request timeout. Mitigation: startup preload and clear startup failure.
  - Medium x High: missing eSpeak NG or incompatible NVIDIA/CUDA runtime. Mitigation: document prerequisites and treat preload failure as deploy-blocking.
  - Medium x Medium: MP3 encoding support differs by host libsndfile build. Mitigation: verify on deployment image; if unsupported, stop rollout before route switch.
- Rollback: restore `edge-tts` dependency and previous service module, then rerun route and test suite unchanged.

### Phase 2: Route Compatibility

- Status: complete
- Blocked by: Phase 1
- Files: `backend/text_to_speech_routes.py`, `backend/assistant_routes.py`
- Work:
  1. Remove Edge-specific imports/exceptions from `backend/text_to_speech_routes.py:9-16` and `backend/assistant_routes.py:14,30-35,165-174`.
  2. Keep route paths, validation, OpenAPI binary schema, `audio/mpeg` media type, and attachment filenames unchanged.
  3. Keep no-audio mapped to `502`; unexpected local synthesis failures are not wrapped.
- Backward compatibility: no client-visible request or response contract change; only backend provider swap.
- Rollback: point routes back to the restored Edge service and exception classes from Phase 1 rollback.

### Phase 3: Tests, Live Checks, Docs

- Status: complete
- Blocked by: Phases 1-2
- Files: `backend/tests/test_text_to_speech_service.py`, `backend/tests/test_text_to_speech_endpoint.py`, `backend/tests/test_app_routes.py`, `backend/tests/test_live_voice_assistant_endpoint.py`, `backend/tests/test_voice_assistant_live_smoke.py`, `backend/README.md`, `backend/docs/GPU_SETUP.md`
- Work:
  1. Replace Edge voice assertions with VieNeu service assertions; keep HTTP contract assertions as MP3.
  2. Add preload/warmup tests around startup path and no-preload test env behavior.
  3. Update live tests so they no longer depend on Edge-specific exceptions or voice names.
  4. Update backend docs to state: local VieNeu SDK, GPU intent, eSpeak NG requirement, first-run cache/warmup, and preserved MP3 output.
- Test matrix:
  - Unit: service preload, timeout mapping, no-audio path, MP3 encoding output non-empty.
  - Integration: `/tts` and `/v1/voice/assistant` still emit `audio/mpeg`, same filenames, same validation errors.
  - Live: GPU-capable host can synthesize `/tts` and `/v1/voice/assistant` after preload.
- Rollback: revert docs/tests only after runtime rollback is confirmed.

## Success Criteria

- `backend/text_to_speech_service.py` contains no `edge_tts` import or Edge voice list.
- `POST /tts` still returns `audio/mpeg` and `attachment; filename="speech.mp3"`.
- `POST /v1/voice/assistant` still returns `audio/mpeg` and `attachment; filename="assistant-speech.mp3"`.
- Startup preload catches missing model/runtime prerequisites before serving traffic.
- `uv run python -m compileall .` passes in `backend`.
- Target pytest slices pass without network Edge TTS access.

## Verification Commands

```bash
cd /home/mcs/Workspaces/ai-voice-first/backend
uv lock
uv sync
uv run python -m compileall .
uv run pytest tests/test_text_to_speech_service.py tests/test_text_to_speech_endpoint.py tests/test_app_routes.py -q
RUN_LIVE_VOICE_ENDPOINT=1 uv run pytest tests/test_live_voice_assistant_endpoint.py -q
RUN_LIVE_VOICE_ASSISTANT_SMOKE=1 uv run pytest tests/test_voice_assistant_live_smoke.py -q
```

## File Ownership

- Phase 1 owns runtime/dependency/bootstrap files only.
- Phase 2 owns route files only.
- Phase 3 owns tests and docs only.

## Open Questions / Risks

- Should startup fail hard when GPU is unavailable, or is CPU fallback acceptable for dev only? User asked for GPU intent, so production should likely fail closed.
- Installed `vieneu==2.7.0` exposes `mode="turbo_gpu"` for the exact CUDA Turbo path; implementation uses that mode.
- `vieneu[gpu]` extras resolution and deployment-image MP3 encoding support must be proven on the real target host, not just locally.
