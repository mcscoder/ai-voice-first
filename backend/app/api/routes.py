import asyncio
import json
from collections.abc import Iterator

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, field_validator
from starlette.background import BackgroundTask

from app.core.config import TtsVoice, config
from app.services.assistant import assistant_service
from app.services.assistant.telemetry import assistant_telemetry
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


@router.get("/v1/voice/assistant/telemetry")
def voice_assistant_telemetry() -> dict[str, object]:
    return assistant_telemetry.payload()


@router.get("/v1/voice/assistant/telemetry/stream")
def voice_assistant_telemetry_stream() -> StreamingResponse:
    def event_lines() -> Iterator[str]:
        for snapshot in assistant_telemetry.subscribe(keepalive_seconds=1.0):
            if snapshot is None:
                yield ": keep-alive\n\n"
                continue

            yield assistant_telemetry.sse_event(snapshot)

    return StreamingResponse(
        event_lines(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        },
    )


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


@router.post(
    "/v1/voice/assistant/stream",
    responses={
        200: {
            "content": {
                "application/x-ndjson": {
                    "schema": {"type": "string"},
                },
            },
            "description": "Streaming assistant events",
        },
    },
    response_class=StreamingResponse,
)
async def voice_assistant_stream(
    file: UploadFile = File(...),
    language: str | None = Form(None),
) -> StreamingResponse:
    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    response_holder: dict[str, str] = {}

    def event_lines() -> Iterator[bytes]:
        for event in assistant_service.stream_events(
            audio_bytes,
            language,
            response_holder,
        ):
            yield (json.dumps(event) + "\n").encode("utf-8")

    return StreamingResponse(
        event_lines(),
        media_type="application/x-ndjson",
        background=BackgroundTask(
            assistant_service.persist_streamed_response,
            response_holder,
        ),
    )
