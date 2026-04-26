# Fix TTS No Audio

**Date**: 2026-04-26 17:18
**Severity**: Medium
**Component**: `backend/text_to_speech_service.py`, `backend/text_to_speech_routes.py`
**Status**: Resolved

## What Happened

Swagger test for `POST /tts` returned `500 Internal Server Error` for accented
Vietnamese text: `xin chào, hôm nay bạn khỏe không?`.

## Technical Details

- Direct synthesis reproduced `edge_tts.exceptions.NoAudioReceived` with
  `vi-VN-HoaiMyNeural`.
- The same text succeeded with `vi-VN-NamMinhNeural`.
- Added Vietnamese voice fallback: HoaiMy first, NamMinh second.
- Mapped upstream timeout to `504` and Edge TTS failures/no-audio to `502`.
- Added regression tests for fallback and stable HTTP errors.

## Validation

- `uv run python -m compileall .` passed from `backend`.
- `uv run pytest` passed from `backend`: 21 tests.
- Live FastAPI ASGI request for the failing payload returned `200 audio/mpeg`
  with 17856 bytes.

## Next Steps

- Keep auth, rate limiting, concurrency caps, and body limits on the public
  exposure backlog.
