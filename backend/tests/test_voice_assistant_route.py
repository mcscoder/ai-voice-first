import base64
import json

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


def test_voice_assistant_stream_returns_ordered_events(monkeypatch) -> None:
    calls: dict[str, object] = {}

    def transcribe(audio: bytes, language: str | None) -> AsrResult:
        return AsrResult(text="Hello", language=language or "English", model="test")

    def search_memories(query: str, user_id: str) -> list[str]:
        calls["search"] = {"query": query, "user_id": user_id}
        return ["User likes short answers."]

    def stream_response(query: str, memories: list[str]):
        calls["stream"] = {"query": query, "memories": memories}
        yield "Hi there."

    def synthesize(text: str, voice: object | None) -> TtsResult:
        calls["tts"] = {"text": text, "voice": voice}
        return TtsResult(audio=b"wav-chunk", media_type="audio/wav")

    monkeypatch.setattr(routes.assistant_service.asr, "transcribe", transcribe)
    monkeypatch.setattr(routes.assistant_service.memory, "search_memories", search_memories)
    monkeypatch.setattr(routes.assistant_service.memory, "stream_response", stream_response)
    monkeypatch.setattr(routes.assistant_service.tts, "synthesize", synthesize)

    response = create_client().post(
        "/v1/voice/assistant/stream",
        data={"language": "en"},
        files={"file": ("speech.wav", b"audio-bytes", "audio/wav")},
    )

    assert response.status_code == 200
    events = [json.loads(line) for line in response.text.strip().splitlines()]
    assert events == [
        {"type": "asr", "text": "Hello", "language": "en", "model": "test"},
        {"type": "text_delta", "text": "Hi there."},
        {
            "type": "audio",
            "sequence": 0,
            "media_type": "audio/wav",
            "audio": base64.b64encode(b"wav-chunk").decode("ascii"),
        },
        {"type": "done", "text": "Hi there."},
    ]
    assert response.headers["content-type"].startswith("application/x-ndjson")
    assert calls["search"] == {"query": "Hello", "user_id": DEFAULT_USER_ID}
    assert calls["stream"] == {
        "query": "Hello",
        "memories": ["User likes short answers."],
    }
    assert calls["tts"] == {"text": "Hi there.", "voice": None}


def test_voice_assistant_stream_persists_after_done(monkeypatch) -> None:
    persisted: list[dict[str, str]] = []

    def transcribe(audio: bytes, language: str | None) -> AsrResult:
        return AsrResult(text="Remember this", language="English", model="test")

    def stream_response(query: str, memories: list[str]):
        yield "Saved."

    def synthesize(text: str, voice: object | None) -> TtsResult:
        assert persisted == []
        return TtsResult(audio=b"wav-chunk", media_type="audio/wav")

    def persist_conversation(query: str, response_text: str, user_id: str) -> None:
        persisted.append(
            {"query": query, "response_text": response_text, "user_id": user_id}
        )

    monkeypatch.setattr(routes.assistant_service.asr, "transcribe", transcribe)
    monkeypatch.setattr(routes.assistant_service.memory, "search_memories", lambda *_: [])
    monkeypatch.setattr(routes.assistant_service.memory, "stream_response", stream_response)
    monkeypatch.setattr(routes.assistant_service.tts, "synthesize", synthesize)
    monkeypatch.setattr(
        routes.assistant_service.memory,
        "persist_conversation",
        persist_conversation,
    )

    response = create_client().post(
        "/v1/voice/assistant/stream",
        data={"language": "en"},
        files={"file": ("speech.wav", b"audio-bytes", "audio/wav")},
    )

    assert response.status_code == 200
    assert json.loads(response.text.strip().splitlines()[-1]) == {
        "type": "done",
        "text": "Saved.",
    }
    assert persisted == [
        {
            "query": "Remember this",
            "response_text": "Saved.",
            "user_id": DEFAULT_USER_ID,
        }
    ]


def test_voice_assistant_stream_emits_known_service_errors(monkeypatch) -> None:
    def transcribe(audio: bytes, language: str | None) -> AsrResult:
        raise UnsupportedAsrLanguageError("Unsupported language.")

    monkeypatch.setattr(routes.assistant_service.asr, "transcribe", transcribe)

    response = create_client().post(
        "/v1/voice/assistant/stream",
        data={"language": "fr"},
        files={"file": ("speech.wav", b"audio-bytes", "audio/wav")},
    )

    assert response.status_code == 200
    assert [json.loads(line) for line in response.text.strip().splitlines()] == [
        {"type": "error", "message": "Unsupported language."}
    ]

