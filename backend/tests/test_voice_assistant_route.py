from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from app.api import routes
from app.services.asr import AsrResult, UnsupportedAsrLanguageError
from app.services.memory import DEFAULT_USER_ID, MemoryReply
from app.services.tts import TtsResult


def create_client() -> TestClient:
    app = FastAPI()
    app.include_router(routes.router)
    return TestClient(app)


def test_voice_assistant_returns_generated_audio(monkeypatch) -> None:
    calls: dict[str, object] = {}

    def transcribe(audio: bytes, language: str | None) -> AsrResult:
        calls["asr"] = {"audio": audio, "language": language}
        return AsrResult(text="What should I do today?", language="English", model="test")

    def respond(text: str, user_id: str) -> MemoryReply:
        calls["memory"] = {"text": text, "user_id": user_id}
        return MemoryReply(text="You should review your plan.", user_id=user_id)

    def synthesize(text: str, voice: object | None) -> TtsResult:
        calls["tts"] = {"text": text, "voice": voice}
        return TtsResult(audio=b"wav-bytes", media_type="audio/wav")

    monkeypatch.setattr(routes.assistant_service.asr, "transcribe", transcribe)
    monkeypatch.setattr(routes.assistant_service.memory, "respond", respond)
    monkeypatch.setattr(routes.assistant_service.tts, "synthesize", synthesize)

    response = create_client().post(
        "/v1/voice/assistant",
        data={"language": "en"},
        files={"file": ("speech.wav", b"audio-bytes", "audio/wav")},
    )

    assert response.status_code == 200
    assert response.content == b"wav-bytes"
    assert response.headers["content-type"] == "audio/wav"
    assert calls["asr"] == {"audio": b"audio-bytes", "language": "en"}
    assert calls["memory"] == {
        "text": "What should I do today?",
        "user_id": DEFAULT_USER_ID,
    }
    assert calls["tts"] == {"text": "You should review your plan.", "voice": None}


def test_voice_assistant_rejects_empty_upload() -> None:
    response = create_client().post(
        "/v1/voice/assistant",
        data={"language": "en"},
        files={"file": ("empty.wav", b"", "audio/wav")},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Uploaded file is empty."}


def test_voice_assistant_propagates_service_errors(monkeypatch) -> None:
    def transcribe(audio: bytes, language: str | None) -> AsrResult:
        raise UnsupportedAsrLanguageError("Unsupported language.")

    monkeypatch.setattr(routes.assistant_service.asr, "transcribe", transcribe)

    with pytest.raises(UnsupportedAsrLanguageError, match="Unsupported language."):
        create_client().post(
            "/v1/voice/assistant",
            data={"language": "fr"},
            files={"file": ("speech.wav", b"audio-bytes", "audio/wav")},
        )
