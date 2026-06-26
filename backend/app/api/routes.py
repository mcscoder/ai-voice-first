import asyncio
import json
from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response, StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, field_validator
from starlette.background import BackgroundTask

from app.api.auth import (
    AuthTokenResponse,
    AuthUserResponse,
    CurrentUser,
    EmailPasswordRequest,
    RefreshTokenRequest,
    auth_http_error,
    bearer_scheme,
    login_user,
    logout_user,
    refresh_user_token,
    register_user,
)
from app.core.config import TtsVoice, config
from app.services.assistant import assistant_service
from app.services.assistant.telemetry import assistant_telemetry
from app.services.assistant.telemetry_payload import (
    telemetry_sse_event,
    with_service_metadata,
)
from app.services.auth import AuthConfigError, InvalidCredentialsError, auth_service
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


def telemetry_user_id(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
) -> str | None:
    if config.telemetry.public_stream == "enabled":
        return None
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise auth_http_error()
    try:
        return auth_service.user_from_access_token(credentials.credentials).id
    except (AuthConfigError, InvalidCredentialsError) as error:
        raise auth_http_error() from error


@router.get("/")
def read_root() -> dict[str, str]:
    return {"message": "AI Voice First backend is running"}


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/auth/register", response_model=AuthTokenResponse)
def auth_register(request: EmailPasswordRequest) -> AuthTokenResponse:
    return register_user(request)


@router.post("/auth/login", response_model=AuthTokenResponse)
def auth_login(request: EmailPasswordRequest) -> AuthTokenResponse:
    return login_user(request)


@router.post("/auth/refresh", response_model=AuthTokenResponse)
def auth_refresh(request: RefreshTokenRequest) -> AuthTokenResponse:
    return refresh_user_token(request)


@router.post("/auth/logout")
def auth_logout(request: RefreshTokenRequest, user: CurrentUser) -> dict[str, str]:
    return logout_user(request, user)


@router.get("/auth/me", response_model=AuthUserResponse)
def auth_me(user: CurrentUser) -> AuthUserResponse:
    return AuthUserResponse(id=user.id, email=user.email)


@router.get("/v1/voice/assistant/telemetry/stream")
def voice_assistant_telemetry_stream(
    user_id: Annotated[str | None, Depends(telemetry_user_id)],
) -> StreamingResponse:
    def event_lines() -> Iterator[str]:
        for snapshot in assistant_telemetry.subscribe(
            keepalive_seconds=1.0,
            user_id=user_id,
        ):
            if snapshot is None:
                yield ": keep-alive\n\n"
                continue

            yield telemetry_sse_event(with_service_metadata(snapshot))

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
    user: CurrentUser,
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
async def text_to_speech(request: TtsRequest, user: CurrentUser) -> Response:
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
    user: CurrentUser,
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
        user.id,
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
    user: CurrentUser,
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
            user.id,
        ):
            yield (json.dumps(event) + "\n").encode("utf-8")

    return StreamingResponse(
        event_lines(),
        media_type="application/x-ndjson",
        background=BackgroundTask(
            assistant_service.stream_persistence.persist_streamed_response,
            response_holder,
        ),
    )
