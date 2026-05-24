from __future__ import annotations

import logging
import asyncio
import os
import tempfile
import threading
from pathlib import Path
from typing import Annotated, Literal

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from edge_tts.exceptions import EdgeTTSException

from config import env_flag
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
    TranscriptionService,
)
from text_to_speech_service import (
    MAX_TEXT_LENGTH,
    SUPPORTED_LANGUAGE_VOICES,
    TextToSpeechNoAudioError,
    synthesize_speech_with_fallback,
)
from memory import MemoryService
from personality import PersonalityService


ASSISTANT_REQUEST_TIMEOUT_SECONDS = 45

router = APIRouter()
transcription_service = TranscriptionService()
assistant_service = VoiceAssistantService()
personality_service = PersonalityService(default_personality=os.getenv("ASSISTANT_PERSONALITY", "serious"))
logger = logging.getLogger(__name__)
store_memories_after_response = env_flag("ASSISTANT_STORE_MEMORIES", True)
use_memory_context = env_flag("ASSISTANT_USE_MEMORY_CONTEXT", True)


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
    language: Annotated[Literal["vi", "en"] | None, Form()] = None,
) -> Response:
    try:
        return await asyncio.wait_for(
            _voice_assistant_impl(file=file, language=language),
            timeout=ASSISTANT_REQUEST_TIMEOUT_SECONDS,
        )
    except TimeoutError as exc:
        raise HTTPException(
            status_code=504,
            detail="Voice assistant request timed out.",
        ) from exc


async def _voice_assistant_impl(
    file: UploadFile,
    language: str | None,
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
        transcription = transcription_service.transcribe(
            temp_path,
            transcription_language,
        )
        transcript = str(transcription.get("text", "")).strip()
        if not transcript:
            raise HTTPException(status_code=400, detail="No speech detected.")

        assistant_language = _resolve_assistant_language(
            requested_language=language,
            detected_language=transcription.get("language"),
        )
        memory_context = ""
        if use_memory_context:
            memory_context = await MemoryService().build_context("local-user", transcript)
        reply = await assistant_service.complete(
            transcript,
            assistant_language,
            memory_context=memory_context or None,
            personality=personality_service.resolve_personality(None),
        )
        reply_text = reply.strip()
        if len(reply_text) > MAX_TEXT_LENGTH:
            raise HTTPException(
                status_code=502,
                detail="Assistant reply is too long for speech synthesis.",
            )

        audio = await synthesize_speech_with_fallback(
            reply_text,
            SUPPORTED_LANGUAGE_VOICES[assistant_language],
        )
        if store_memories_after_response:
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
    except EdgeTTSException as exc:
        raise HTTPException(
            status_code=502,
            detail="Text-to-speech service failed.",
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


def _resolve_assistant_language(
    *,
    requested_language: str | None,
    detected_language: object,
) -> AssistantLanguage:
    if requested_language in {"en", "vi"}:
        return requested_language

    detected = str(detected_language or "").lower()
    if detected.startswith("vi"):
        return "vi"
    if detected.startswith("en"):
        return "en"
    return "vi"
