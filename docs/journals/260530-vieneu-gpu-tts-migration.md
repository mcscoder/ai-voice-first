# VieNeu GPU TTS Migration

**Date**: 2026-05-30
**Severity**: Medium
**Component**: `backend/text_to_speech_service.py`, `backend/transcription_service.py`, `backend/pyproject.toml`
**Status**: Resolved

## What Happened

Removed Edge TTS and replaced backend speech synthesis with local VieNeu TTS v2 Turbo
using `pnnbao-ump/VieNeu-TTS-v2-Turbo` in `turbo_gpu` mode on CUDA.

## Technical Details

- Added `vieneu[gpu]` and `onnxruntime-gpu`.
- Excluded CPU `onnxruntime` so VieNeu uses the GPU provider.
- Kept Sherpa CUDA wheel discovery in `tool.uv.find-links`.
- Kept MP3 API contract by encoding VieNeu 24 kHz waveform output with `soundfile`.
- Added startup warmup for CUDA provider, model load, inference, and MP3 encode.
- Moved ASR and TTS into separate local worker processes.
- FastAPI talks to both models through local multiprocessing pipes, not HTTP.

## Validation

- `python -m py_compile text_to_speech_service.py transcription_service.py transcription_routes.py assistant_routes.py main.py tests/test_app_routes.py tests/test_text_to_speech_service.py` passed.
- `pytest tests/test_text_to_speech_service.py tests/test_text_to_speech_endpoint.py tests/test_app_routes.py -q` passed: 29 passed.
- `pytest -q` passed: 36 passed, 4 skipped.
- `uv run uvicorn main:app --host 127.0.0.1 --port 8023` reached `Application startup complete`.
- ONNX Runtime providers include `CUDAExecutionProvider`.
- Edge TTS reference scan returned no backend runtime matches.

## Lessons Learned

- `uv` can keep Sherpa CUDA wheels reproducible through `tool.uv.find-links`; no need to pass `-f` manually every sync.
- Native CUDA libraries are isolated per model process, so ASR and TTS can recover without sharing one Python runtime.

## Unresolved Questions

None.
