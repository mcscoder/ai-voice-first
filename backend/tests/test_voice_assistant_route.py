import base64
import json

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from app.api import routes
from app.services.assistant.telemetry import assistant_telemetry
from app.services.asr import AsrResult, UnsupportedAsrLanguageError
from app.services.memory import (
    DEFAULT_USER_ID,
    MemoryPersistResult,
    MemoryReply,
    MemorySearchResult,
)
from app.services.tts import TtsResult


@pytest.fixture(autouse=True)
def reset_assistant_telemetry() -> None:
    assistant_telemetry.reset()


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

    def search_memory_results(query: str, user_id: str) -> list[MemorySearchResult]:
        calls["search"] = {"query": query, "user_id": user_id}
        return [
            MemorySearchResult.from_mem0(
                {
                    "id": "memory-id",
                    "memory": "User likes short answers.",
                    "score": 0.91,
                    "created_at": "2026-06-25T04:08:26+00:00",
                },
            )
        ]

    def stream_response(
        query: str,
        memories: list[MemorySearchResult],
        messages: list[dict[str, str]],
    ):
        calls["stream"] = {
            "query": query,
            "memories": memories,
            "messages": messages,
        }
        yield "Hi there."

    def synthesize(text: str, voice: object | None) -> TtsResult:
        calls["tts"] = {"text": text, "voice": voice}
        return TtsResult(audio=b"wav-chunk", media_type="audio/wav")

    monkeypatch.setattr(routes.assistant_service.asr, "transcribe", transcribe)
    monkeypatch.setattr(
        routes.assistant_service.memory,
        "search_memory_results",
        search_memory_results,
    )
    monkeypatch.setattr(routes.assistant_service.memory, "stream_response", stream_response)
    monkeypatch.setattr(
        routes.assistant_service.memory,
        "persist_conversation",
        lambda *_: None,
    )
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
    stream_call = calls["stream"]
    assert isinstance(stream_call, dict)
    messages = stream_call.pop("messages")
    assert stream_call == {
        "query": "Hello",
        "memories": [
            MemorySearchResult.from_mem0(
                {
                    "id": "memory-id",
                    "memory": "User likes short answers.",
                    "score": 0.91,
                    "created_at": "2026-06-25T04:08:26+00:00",
                },
            )
        ],
    }
    assert isinstance(messages, list)
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "system"
    assert messages[2] == {"role": "user", "content": "Hello"}
    prompt = messages[1]["content"]
    assert "Relevant memories CSV:" in prompt
    assert "memory,created_at,updated_at" in prompt
    assert "User likes short answers." in prompt
    assert "2026-06-25T04:08:26+00:00" in prompt
    assert "memory-id" not in prompt
    assert "0.91" not in prompt
    assert calls["tts"] == {"text": "Hi there.", "voice": None}


def test_voice_assistant_stream_persists_after_done(monkeypatch) -> None:
    persisted: list[dict[str, str]] = []

    def transcribe(audio: bytes, language: str | None) -> AsrResult:
        return AsrResult(text="Remember this", language="English", model="test")

    def stream_response(
        query: str,
        memories: list[MemorySearchResult],
        messages: list[dict[str, str]],
    ):
        yield "Saved."

    def synthesize(text: str, voice: object | None) -> TtsResult:
        assert persisted == []
        return TtsResult(audio=b"wav-chunk", media_type="audio/wav")

    def persist_conversation(query: str, response_text: str, user_id: str) -> None:
        persisted.append(
            {"query": query, "response_text": response_text, "user_id": user_id}
        )

    monkeypatch.setattr(routes.assistant_service.asr, "transcribe", transcribe)
    monkeypatch.setattr(
        routes.assistant_service.memory,
        "search_memory_results",
        lambda *_: [],
    )
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


def test_voice_assistant_stream_records_pipeline_telemetry(monkeypatch) -> None:
    def transcribe(audio: bytes, language: str | None) -> AsrResult:
        return AsrResult(text="Remember this", language="English", model="test")

    def stream_response(
        query: str,
        memories: list[MemorySearchResult],
        messages: list[dict[str, str]],
    ):
        yield "Saved."

    def synthesize(text: str, voice: object | None) -> TtsResult:
        return TtsResult(audio=b"wav-chunk", media_type="audio/wav")

    monkeypatch.setattr(routes.assistant_service.asr, "transcribe", transcribe)
    monkeypatch.setattr(
        routes.assistant_service.memory,
        "search_memory_results",
        lambda *_: [
            MemorySearchResult.from_mem0(
                {
                    "id": "memory-id",
                    "memory": "User likes concise answers.",
                    "score": 0.82,
                    "created_at": "2026-06-25T04:08:26+00:00",
                    "updated_at": "2026-06-25T05:40:29+00:00",
                    "metadata": {"topic": "preferences"},
                },
            )
        ],
    )
    monkeypatch.setattr(routes.assistant_service.memory, "stream_response", stream_response)
    monkeypatch.setattr(routes.assistant_service.tts, "synthesize", synthesize)
    monkeypatch.setattr(
        routes.assistant_service.memory,
        "persist_conversation",
        lambda *_: None,
    )

    response = create_client().post(
        "/v1/voice/assistant/stream",
        data={"language": "en"},
        files={"file": ("speech.wav", b"audio-bytes", "audio/wav")},
    )

    assert response.status_code == 200

    telemetry_response = create_client().get("/v1/voice/assistant/telemetry")
    assert telemetry_response.status_code == 200
    payload = telemetry_response.json()
    assert payload["summary"] == {"active_count": 0, "recent_count": 1}

    run = payload["recent_runs"][0]
    stages = {stage["name"]: stage for stage in run["stages"]}
    assert run["status"] == "done"
    assert stages["asr"]["metadata"]["transcript"] == "Remember this"
    assert stages["memory_search"]["metadata"]["memory_count"] == 1
    assert stages["memory_search"]["metadata"]["memories"] == [
        {
            "id": "memory-id",
            "memory": "User likes concise answers.",
            "score": 0.82,
            "created_at": "2026-06-25T04:08:26+00:00",
            "updated_at": "2026-06-25T05:40:29+00:00",
            "metadata": {"topic": "preferences"},
        }
    ]
    llm_metadata = stages["llm_response_stream"]["metadata"]
    assert llm_metadata["characters"] == len("Saved.")
    assert llm_metadata["reply_chunks"] == [{"index": 1, "text": "Saved."}]
    assert llm_metadata["prompt_messages"][0]["role"] == "system"
    assert llm_metadata["prompt_messages"][1]["role"] == "system"
    assert llm_metadata["prompt_messages"][2] == {
        "role": "user",
        "content": "Remember this",
    }
    prompt = llm_metadata["prompt_messages"][1]["content"]
    assert "Relevant memories CSV:" in prompt
    assert "memory,created_at,updated_at" in prompt
    assert "User likes concise answers." in prompt
    assert "2026-06-25T04:08:26+00:00" in prompt
    assert "2026-06-25T05:40:29+00:00" in prompt
    assert "id,memory,user_id,categories,created_at,updated_at,score" not in prompt
    assert "memory-id" not in prompt
    assert "0.82" not in prompt
    assert stages["tts_synthesis"]["metadata"]["chunk_count"] == 1
    assert stages["tts_synthesis"]["metadata"]["current_chunk"] is None
    tts_chunks = stages["tts_synthesis"]["metadata"]["chunks"]
    assert len(tts_chunks) == 1
    assert tts_chunks[0]["sequence"] == 0
    assert tts_chunks[0]["text"] == "Saved."
    assert tts_chunks[0]["status"] == "streamed"
    assert isinstance(tts_chunks[0]["duration_ms"], int | float)
    assert tts_chunks[0]["duration_ms"] >= 0
    assert stages["mem0_persist_background"]["metadata"] == {"persisted": True}


def test_voice_assistant_stream_records_memory_persist_actions(monkeypatch) -> None:
    def transcribe(audio: bytes, language: str | None) -> AsrResult:
        return AsrResult(text="Remember this", language="English", model="test")

    def stream_response(
        query: str,
        memories: list[MemorySearchResult],
        messages: list[dict[str, str]],
    ):
        yield "Saved."

    def synthesize(text: str, voice: object | None) -> TtsResult:
        return TtsResult(audio=b"wav-chunk", media_type="audio/wav")

    persist_result = MemoryPersistResult(
        actions=[
            {
                "id": "memory-id",
                "memory": "Nguyên nợ tôi năm mươi ngàn.",
                "event": "UPDATE",
                "previous_memory": "Nguyên nợ tôi tiền.",
            },
            {
                "id": "1",
                "memory": "Đang dự định in lại tài liệu",
                "event": "NONE",
            },
        ],
        action_counts={"UPDATE": 1, "NONE": 1},
        raw_result=None,
    )

    monkeypatch.setattr(routes.assistant_service.asr, "transcribe", transcribe)
    monkeypatch.setattr(
        routes.assistant_service.memory,
        "search_memory_results",
        lambda *_: [],
    )
    monkeypatch.setattr(routes.assistant_service.memory, "stream_response", stream_response)
    monkeypatch.setattr(routes.assistant_service.tts, "synthesize", synthesize)
    monkeypatch.setattr(
        routes.assistant_service.memory,
        "persist_conversation",
        lambda *_: persist_result,
    )

    response = create_client().post(
        "/v1/voice/assistant/stream",
        data={"language": "en"},
        files={"file": ("speech.wav", b"audio-bytes", "audio/wav")},
    )

    assert response.status_code == 200

    payload = create_client().get("/v1/voice/assistant/telemetry").json()
    run = payload["recent_runs"][0]
    stages = {stage["name"]: stage for stage in run["stages"]}
    persist_metadata = stages["mem0_persist_background"]["metadata"]

    assert persist_metadata["persisted"] is True
    assert persist_metadata["action_counts"] == {"UPDATE": 1, "NONE": 1}
    assert persist_metadata["memory_actions"] == persist_result.actions


def test_voice_assistant_telemetry_endpoint_returns_service_metadata() -> None:
    response = create_client().get("/v1/voice/assistant/telemetry")

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"] == {"active_count": 0, "recent_count": 0}
    assert payload["services"]["llm_model"] == "deepseek-v4-flash"
    assert payload["services"]["llm_thinking"] == "disabled"
    assert payload["services"]["asr_model"] == "Qwen/Qwen3-ASR-0.6B"


def test_voice_assistant_telemetry_stream_returns_sse_event() -> None:
    response = routes.voice_assistant_telemetry_stream()
    assert response.media_type == "text/event-stream"
    assert response.headers["cache-control"] == "no-cache"
    assert response.headers["x-accel-buffering"] == "no"

    event = assistant_telemetry.sse_event(assistant_telemetry.snapshot())
    lines = event.splitlines()
    assert lines[0] == "event: telemetry"
    data_line = lines[1]
    assert data_line.startswith("data: ")
    payload = json.loads(data_line.removeprefix("data: "))
    assert payload["summary"] == {"active_count": 0, "recent_count": 0}
    assert payload["services"]["llm_model"] == "deepseek-v4-flash"
    assert payload["services"]["llm_thinking"] == "disabled"


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
