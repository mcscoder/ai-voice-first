# Scout Report: ASR Undecodable M4A Crash

## Scope

- Request path under review: `POST /v1/voice/assistant` and shared ASR service.
- Root `README.md` is absent in repo root; backend contract was verified from `backend/README.md`.

## Verified Data Flow

1. `backend/assistant_routes.py:84-105` saves the upload to a temp file and calls `transcription_service.transcribe(temp_path, transcription_language)`.
2. `backend/transcription_service.py:157-177` sends `{cmd: "RUN", file_path, language}` over the pipe and blocks on `recv()`.
3. `backend/transcription_service.py:180-197` receives the job in the child and calls `_LocalTranscriptionModel.transcribe(...)`.
4. `backend/transcription_service.py:87-103` loads the audio with `soundfile.read()` and `soundfile.info()` before decoding.

## Verified Failure Mode

- The worker loop has no per-job `try/except` at `backend/transcription_service.py:180-197`.
- The parent side has no `EOFError` or broken-pipe translation at `backend/transcription_service.py:167-177`.
- Result: if `soundfile` rejects the container, the child exits, the parent sees pipe EOF, and the request becomes an untyped 500 instead of a mapped transcription error.

## Existing HTTP Contract

- `backend/assistant_routes.py:157-160` already maps `AudioTranscriptionError` to 400 and `BackendTranscriptionError` to 500.
- `backend/transcription_routes.py:50-53` uses the same mapping.
- `backend/README.md:101-110` documents 400 for empty uploads and empty transcripts, but not unreadable audio.

## Existing Test Coverage Gap

- `/transcribe` currently covers empty upload and success only in `backend/tests/test_app_routes.py:23-67`.
- `/v1/voice/assistant` currently covers success, empty upload, and empty transcript in `backend/tests/test_app_routes.py:141-177` and `backend/tests/test_app_routes.py:331-363`.
- No current test covers decode failure, worker crash, or EOF translation.

## Minimum Safe Fix

- Keep the route contract and dependency set unchanged.
- Harden `backend/transcription_service.py` to:
  - convert known decode failures into `AudioTranscriptionError`
  - send structured error payloads from the worker instead of crashing
  - map unexpected worker exits to `BackendTranscriptionError`
- Add offline regression tests for service and route behavior.

## Unresolved Questions

None.
