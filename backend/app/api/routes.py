import asyncio

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, field_validator

from app.core.config import TtsVoice, config
from app.services.assistant import assistant_service
from app.services.asr import asr_service
from app.services.tts import tts_service


# Keep base routes together until the API surface grows enough to split by feature.
router = APIRouter()


class TtsRequest(BaseModel):
    text: str
    voice: TtsVoice | None = None

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("Text must not be empty.")
        if len(text) > config.tts.max_text_length:
            raise ValueError(
                f"Text must be at most {config.tts.max_text_length} characters."
            )
        return text


@router.get("/")
def read_root() -> dict[str, str]:
    return {"message": "AI Voice First backend is running"}


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/asr")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str | None = Form(None),
) -> dict[str, str | None]:
    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    result = await asyncio.to_thread(
        asr_service.transcribe,
        audio_bytes,
        language,
    )

    return {
        "text": result.text,
        "language": result.language,
        "model": result.model,
        "filename": file.filename,
        "content_type": file.content_type,
    }


@router.post(
    "/tts",
    responses={
        200: {
            "content": {
                "audio/wav": {
                    "schema": {"type": "string", "format": "binary"},
                },
            },
            "description": "Generated WAV audio",
        },
    },
    response_class=Response,
)
async def text_to_speech(request: TtsRequest) -> Response:
    result = await asyncio.to_thread(
        tts_service.synthesize,
        request.text,
        request.voice,
    )

    return Response(
        content=result.audio,
        media_type=result.media_type,
        headers={"Content-Disposition": 'attachment; filename="speech.wav"'},
    )


@router.post(
    "/v1/voice/assistant",
    responses={
        200: {
            "content": {
                "audio/wav": {
                    "schema": {"type": "string", "format": "binary"},
                },
            },
            "description": "Generated assistant WAV audio",
        },
    },
    response_class=Response,
)
async def voice_assistant(
    file: UploadFile = File(...),
    language: str | None = Form(None),
) -> Response:
    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    result = await asyncio.to_thread(
        assistant_service.respond,
        audio_bytes,
        language,
    )

    return Response(
        content=result.audio,
        media_type=result.media_type,
        headers={"Content-Disposition": 'attachment; filename="assistant.wav"'},
    )
