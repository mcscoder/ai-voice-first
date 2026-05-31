from __future__ import annotations

import logging
import asyncio
import os
import tempfile
import threading
import time
from pathlib import Path
from typing import Annotated, Literal

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import Response

from assistant_memory_policy import (
    should_store_memories,
    should_use_memory_context,
    should_use_memory_for_request,
)
from assistant_service import (
    AssistantEmptyReplyError,
    AssistantServiceError,
    AssistantLanguage,
    AssistantTimeoutError,
    VoiceAssistantService,
)
from transcription_service import (
    AudioTranscriptionError,
    BackendTranscriptionError,
    LanguageOption,
    transcription_service,
)
from text_to_speech_service import (
    MAX_TEXT_LENGTH,
    TextToSpeechNoAudioError,
    synthesize_speech,
)
from memory import MemoryService, should_store_memory_transcript
from personality import PersonalityService


ASSISTANT_REQUEST_TIMEOUT_SECONDS = 45

router = APIRouter()
assistant_service = VoiceAssistantService()
personality_service = PersonalityService(default_personality=os.getenv("ASSISTANT_PERSONALITY", "serious"))
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
    request: Request,
    file: UploadFile = File(...),
    language: Annotated[Literal["vi", "en"] | None, Form()] = None,
) -> Response:
    try:
        return await asyncio.wait_for(
            _voice_assistant_impl(request=request, file=file, language=language),
            timeout=ASSISTANT_REQUEST_TIMEOUT_SECONDS,
        )
    except TimeoutError as exc:
        raise HTTPException(
            status_code=504,
            detail="Voice assistant request timed out.",
        ) from exc


async def _voice_assistant_impl(
    request: Request, file: UploadFile, language: str | None,
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

        transcription_language = (
            LanguageOption(language) if language else LanguageOption.AUTO
        )
        transcription_started_at = time.perf_counter()
        transcription = await transcription_service.transcribe(temp_path, transcription_language)
        transcription_duration = time.perf_counter() - transcription_started_at
        transcript = str(transcription.get("text", "")).strip()
        if not transcript:
            raise HTTPException(status_code=400, detail="No speech detected.")

        assistant_language = _resolve_assistant_language(
            requested_language=language,
            detected_language=transcription.get("language"),
        )
        memory_context = ""
        memory_allowed = should_use_memory_for_request(request)
        if should_use_memory_context() and memory_allowed:
            try:
                memory_context = await MemoryService().build_context("local-user", transcript)
            except Exception:
                logger.exception("Failed to build memory context.")
        assistant_started_at = time.perf_counter()
        reply = await assistant_service.complete(
            transcript,
            assistant_language,
            memory_context=memory_context or None,
            personality=personality_service.resolve_personality(None),
        )
        assistant_duration = time.perf_counter() - assistant_started_at
        reply_text = reply.strip()
        if len(reply_text) > MAX_TEXT_LENGTH:
            raise HTTPException(
                status_code=502,
                detail="Assistant reply is too long for speech synthesis.",
            )

        tts_started_at = time.perf_counter()
        audio = await synthesize_speech(reply_text, assistant_language)
        tts_duration = time.perf_counter() - tts_started_at
        logger.info(
            "voice_assistant_step_durations transcription=%.3fs assistant=%.3fs tts=%.3fs",
            transcription_duration,
            assistant_duration,
            tts_duration,
        )
        if (
            should_store_memories()
            and memory_allowed
            and should_store_memory_transcript(transcript)
        ):
            threading.Thread(
                target=_store_memory_safely,
                args=(transcript,),
                daemon=True,
            ).start()
        return Response(
            content=audio,
            media_type="audio/mpeg",
            headers={"Content-Disposition": 'attachment; filename="assistant-speech.mp3"'},
        )
    except AudioTranscriptionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except BackendTranscriptionError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except AssistantEmptyReplyError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except AssistantTimeoutError as exc:
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except AssistantServiceError as exc:
        raise HTTPException(status_code=502, detail="Assistant service failed.") from exc
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


def _store_memory_safely(transcript: str) -> None:
    try:
        MemoryService().process_transcript_sync("local-user", transcript)
    except Exception:
        logger.exception("Failed to store transcript memory.")


def _resolve_assistant_language(*, requested_language: str | None, detected_language: object) -> AssistantLanguage:
    if requested_language in {"en", "vi"}:
        return requested_language

    detected = str(detected_language or "").lower()
    if detected.startswith("vi"):
        return "vi"
    if detected.startswith("en"):
        return "en"
    return "vi"
