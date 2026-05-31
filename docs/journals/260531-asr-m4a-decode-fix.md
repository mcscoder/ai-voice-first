# ASR M4A Decode Fix

Date: 2026-05-31

## Summary

Android voice uploads use AAC in `.m4a`, but backend ASR tried to read uploads
directly with `soundfile`. libsndfile could not decode that container, the ASR
worker crashed, and the parent surfaced `EOFError` as a raw 500.

## Changes

- Added bounded `ffmpeg` fallback decode for compressed audio that `soundfile`
  cannot read.
- Added structured ASR worker error frames for audio and backend failures.
- Restarted ASR worker on parent receive timeout or disconnect to avoid stale
  pipe responses.
- Added worker logging for backend and unexpected transcription failures.
- Added regression tests for real generated `.m4a`, ffmpeg failure modes, worker
  error propagation, and route-level `400`/`500` mappings.
- Documented `ffmpeg` host requirement in backend docs.

## Verification

- `.venv/bin/python -m py_compile transcription_service.py tests/test_transcription_service.py tests/test_app_routes.py`
- `.venv/bin/python -m pytest tests/test_transcription_service.py tests/test_app_routes.py -q`
  passed: `31 passed in 0.23s`
- `git diff --check` passed for touched files.

## Follow-Up

Full backend pytest still times out at
`tests/test_memory_service.py::test_memory_service_persists_and_retrieves_context`.
That failure reproduced in isolation and is unrelated to this ASR fix.

## Unresolved Questions

None.
