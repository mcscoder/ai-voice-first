from __future__ import annotations

import logging
import asyncio
import os
import tempfile
import time
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import Response

from transcription_service import (
    AudioTranscriptionError,
    BackendTranscriptionError,
    transcription_service,
)
from text_to_speech_service import (
    MAX_TEXT_LENGTH,
    TextToSpeechNoAudioError,
    synthesize_speech,
)
from assistant_service import (
    AssistantService,
)


VOICE_ROUTE_TIMEOUT_SECONDS = 45

router = APIRouter()
assistant_service = AssistantService()
logger = logging.getLogger("uvicorn.error")


@router.post(
    "/v1/voice/assistant",
    response_class=Response,
    responses={
        200: {
            "content": {
                "audio/mpeg": {
                    "schema": {"type": "string", "format": "binary"},
                },
            },
            "description": "Generated assistant speech",
        },
    },
)
async def voice_assistant(
    file: UploadFile = File(...),
) -> Response:
    try:
        return await asyncio.wait_for(
            _voice_assistant_impl(file=file),
            timeout=VOICE_ROUTE_TIMEOUT_SECONDS,
        )
    except TimeoutError as exc:
        raise HTTPException(
            status_code=504,
            detail="Voice assistant request timed out.",
        ) from exc


async def _voice_assistant_impl(
    file: UploadFile,
) -> Response:
    suffix = Path(file.filename or "").suffix or ".bin"
    temp_path: str | None = None

    try:
        audio_bytes = await file.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_path = temp_file.name

            temp_file.write(audio_bytes)

        if not audio_bytes:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        transcription_started_at = time.perf_counter()
        transcription = await transcription_service.transcribe(temp_path)
        transcription_duration = time.perf_counter() - transcription_started_at
        transcript = str(transcription.get("text", "")).strip()
        if not transcript:
            raise HTTPException(status_code=400, detail="No speech detected.")

        assistant_started_at = time.perf_counter()
        reply = await assistant_service.complete("local-user", transcript)
        assistant_duration = time.perf_counter() - assistant_started_at
        reply_text = reply.strip()
        if not reply_text:
            raise HTTPException(status_code=502, detail="Assistant service returned no reply.")
        if len(reply_text) > MAX_TEXT_LENGTH:
            raise HTTPException(
                status_code=502,
                detail="Assistant reply is too long for speech synthesis.",
            )

        tts_started_at = time.perf_counter()
        audio = await synthesize_speech(reply_text)
        tts_duration = time.perf_counter() - tts_started_at
        logger.info(
            "voice_assistant_step_durations transcription=%.3fs assistant=%.3fs tts=%.3fs",
            transcription_duration,
            assistant_duration,
            tts_duration,
        )
        return Response(
            content=audio,
            media_type="audio/mpeg",
            headers={"Content-Disposition": 'attachment; filename="assistant-speech.mp3"'},
        )
    except AudioTranscriptionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except BackendTranscriptionError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except TextToSpeechNoAudioError as exc:
        raise HTTPException(
            status_code=502,
            detail="Text-to-speech service returned no audio.",
        ) from exc
    except TimeoutError as exc:
        raise HTTPException(
            status_code=504,
            detail="Assistant speech synthesis timed out.",
        ) from exc
    finally:
        await file.close()
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
