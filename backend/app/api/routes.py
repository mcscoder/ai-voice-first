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
from app.services.memory import (
    ManagedMemoryItem,
    MemoryCategoryKey,
    MemoryNotFoundError,
    memory_service,
)
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


class MemoryItemResponse(BaseModel):
    id: str
    memory: str
    category: MemoryCategoryKey
    created_at: str | None = None
    updated_at: str | None = None

    @classmethod
    def from_item(cls, item: ManagedMemoryItem) -> "MemoryItemResponse":
        return cls(
            id=item.id,
            memory=item.memory,
            category=item.category,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )


class MemoryListResponse(BaseModel):
    memory_enabled: bool
    memories: list[MemoryItemResponse]


class MemoryMutationRequest(BaseModel):
    memory: str
    category: MemoryCategoryKey

    @field_validator("memory")
    @classmethod
    def validate_memory(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("Memory must not be empty.")
        return text


class MemorySettingsRequest(BaseModel):
    memory_enabled: bool


class MemorySettingsResponse(BaseModel):
    memory_enabled: bool


_VALID_SPEAKING_STYLES = {
    "shortAnswers",
    "detailedAnswers",
    "casual",
    "professional",
}


class PersonalizationResponse(BaseModel):
    nickname: str
    speaking_style: str
    setup_completed: bool


class PersonalizationRequest(BaseModel):
    nickname: str
    speaking_style: str

    @field_validator("nickname")
    @classmethod
    def validate_nickname(cls, value: str) -> str:
        return value.strip()

    @field_validator("speaking_style")
    @classmethod
    def validate_speaking_style(cls, value: str) -> str:
        if value not in _VALID_SPEAKING_STYLES:
            raise ValueError("Invalid speaking_style.")
        return value


class SetupCompletionRequest(BaseModel):
    setup_completed: bool


class VoiceOptionResponse(BaseModel):
    id: TtsVoice
    name: str
    description: str


class VoiceSettingsRequest(BaseModel):
    selected_voice: TtsVoice


class VoiceSettingsResponse(BaseModel):
    selected_voice: TtsVoice
    default_voice: TtsVoice
    voices: list[VoiceOptionResponse]


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


@router.get("/v1/memories", response_model=MemoryListResponse)
def list_memories(user: CurrentUser) -> MemoryListResponse:
    memories = [
        MemoryItemResponse.from_item(item)
        for item in memory_service.list_memories(user.id)
    ]
    return MemoryListResponse(
        memory_enabled=memory_service.is_enabled(user.id),
        memories=memories,
    )


@router.post("/v1/memories", response_model=MemoryItemResponse)
def create_memory(
    request: MemoryMutationRequest,
    user: CurrentUser,
) -> MemoryItemResponse:
    item = memory_service.create_memory(user.id, request.memory, request.category)
    return MemoryItemResponse.from_item(item)


@router.patch("/v1/memories/{memory_id}", response_model=MemoryItemResponse)
def update_memory(
    memory_id: str,
    request: MemoryMutationRequest,
    user: CurrentUser,
) -> MemoryItemResponse:
    try:
        item = memory_service.update_memory(
            user.id,
            memory_id,
            request.memory,
            request.category,
        )
    except MemoryNotFoundError as error:
        raise HTTPException(status_code=404, detail="Memory not found.") from error
    return MemoryItemResponse.from_item(item)


@router.delete("/v1/memories/{memory_id}")
def delete_memory(memory_id: str, user: CurrentUser) -> dict[str, str]:
    try:
        memory_service.delete_memory(user.id, memory_id)
    except MemoryNotFoundError as error:
        raise HTTPException(status_code=404, detail="Memory not found.") from error
    return {"status": "ok"}


@router.put("/v1/memories/settings", response_model=MemorySettingsResponse)
def update_memory_settings(
    request: MemorySettingsRequest,
    user: CurrentUser,
) -> MemorySettingsResponse:
    return MemorySettingsResponse(
        memory_enabled=memory_service.set_enabled(user.id, request.memory_enabled)
    )


@router.get("/v1/profile/personalization", response_model=PersonalizationResponse)
def get_personalization(user: CurrentUser) -> PersonalizationResponse:
    personalization = auth_service.get_personalization(user.id)
    return PersonalizationResponse(
        nickname=personalization.nickname,
        speaking_style=personalization.speaking_style,
        setup_completed=personalization.setup_completed,
    )


@router.put("/v1/profile/personalization", response_model=PersonalizationResponse)
def update_personalization(
    request: PersonalizationRequest,
    user: CurrentUser,
) -> PersonalizationResponse:
    personalization = auth_service.set_personalization(
        user.id,
        nickname=request.nickname,
        speaking_style=request.speaking_style,
    )
    return PersonalizationResponse(
        nickname=personalization.nickname,
        speaking_style=personalization.speaking_style,
        setup_completed=personalization.setup_completed,
    )


@router.put("/v1/profile/setup", response_model=PersonalizationResponse)
def update_profile_setup(
    request: SetupCompletionRequest,
    user: CurrentUser,
) -> PersonalizationResponse:
    auth_service.set_setup_completed(user.id, request.setup_completed)
    personalization = auth_service.get_personalization(user.id)
    return PersonalizationResponse(
        nickname=personalization.nickname,
        speaking_style=personalization.speaking_style,
        setup_completed=personalization.setup_completed,
    )


@router.get("/v1/voice/settings", response_model=VoiceSettingsResponse)
def get_voice_settings(user: CurrentUser) -> VoiceSettingsResponse:
    return VoiceSettingsResponse(
        selected_voice=auth_service.get_voice(user.id),
        default_voice=config.tts.default_voice,
        voices=[
            VoiceOptionResponse(
                id=voice.id,
                name=voice.name,
                description=voice.description,
            )
            for voice in tts_service.list_voice_options()
        ],
    )


@router.put("/v1/voice/settings", response_model=VoiceSettingsResponse)
def update_voice_settings(
    request: VoiceSettingsRequest,
    user: CurrentUser,
) -> VoiceSettingsResponse:
    return VoiceSettingsResponse(
        selected_voice=auth_service.set_voice(user.id, request.selected_voice),
        default_voice=config.tts.default_voice,
        voices=[
            VoiceOptionResponse(
                id=voice.id,
                name=voice.name,
                description=voice.description,
            )
            for voice in tts_service.list_voice_options()
        ],
    )


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

    selected_voice = auth_service.get_voice(user.id)
    result = await asyncio.to_thread(
        assistant_service.respond,
        audio_bytes,
        language,
        user.id,
        selected_voice,
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

    selected_voice = auth_service.get_voice(user.id)
    response_holder: dict[str, str] = {}

    def event_lines() -> Iterator[bytes]:
        for event in assistant_service.stream_events(
            audio_bytes,
            language,
            response_holder,
            user.id,
            selected_voice,
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
