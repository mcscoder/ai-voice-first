from __future__ import annotations

import asyncio
import os
import tempfile
from pathlib import Path
from typing import Annotated, Literal

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from edge_tts.exceptions import EdgeTTSException

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


ASSISTANT_REQUEST_TIMEOUT_SECONDS = 45

router = APIRouter()
transcription_service = TranscriptionService()
assistant_service = VoiceAssistantService()


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
    bytes_written = 0
    temp_path: str | None = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_path = temp_file.name

            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                temp_file.write(chunk)
                bytes_written += len(chunk)

        if bytes_written == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        transcription_language = (
            LanguageOption(language) if language else LanguageOption.AUTO
        )
        transcription = await asyncio.to_thread(
            transcription_service.transcribe,
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
        reply = await assistant_service.complete(transcript, assistant_language)
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
