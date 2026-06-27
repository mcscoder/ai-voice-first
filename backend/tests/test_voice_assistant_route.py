import base64
import json
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from app.api import routes
from app.api.auth import current_user
from app.services.assistant.telemetry import assistant_telemetry
from app.services.assistant.telemetry_payload import (
    telemetry_sse_event,
    with_service_metadata,
)
from app.services.asr import AsrResult, UnsupportedAsrLanguageError
from app.services.auth import AuthenticatedUser
from app.services.memory import (
    MemoryAction,
    MemoryPersistResult,
    MemoryReply,
    MemorySearchResult,
    conversation_history,
)
from app.services.memory.prompt import build_response_messages
from app.services.tts import TtsResult, TtsVoiceOption


@pytest.fixture(autouse=True)
def reset_assistant_telemetry() -> None:
    assistant_telemetry.reset()
    conversation_history.clear()


def create_client() -> TestClient:
    app = FastAPI()
    app.include_router(routes.router)
    app.dependency_overrides[current_user] = lambda: AuthenticatedUser(
        id="test-user",
        email="test@example.com",
    )
    app.dependency_overrides[routes.telemetry_user_id] = lambda: "test-user"
    return TestClient(app)


def create_unauthenticated_client() -> TestClient:
    app = FastAPI()
    app.include_router(routes.router)
    return TestClient(app)


def test_voice_assistant_returns_generated_audio(monkeypatch) -> None:
    calls: dict[str, object] = {}

    def transcribe(audio: bytes, language: str | None) -> AsrResult:
        calls["asr"] = {"audio": audio, "language": language}
        return AsrResult(text="Hôm nay tôi nên làm gì?", language="Vietnamese", model="test")

    def respond(text: str, user_id: str) -> MemoryReply:
        calls["memory"] = {"text": text, "user_id": user_id}
        return MemoryReply(text="You should review your plan.", user_id=user_id)

    def synthesize(text: str, voice: object | None) -> TtsResult:
        calls["tts"] = {"text": text, "voice": voice}
        return TtsResult(audio=b"wav-bytes", media_type="audio/wav")

    monkeypatch.setattr(routes.auth_service, "get_voice", lambda *_: "Ngọc Linh")
    monkeypatch.setattr(routes.assistant_service.asr, "transcribe", transcribe)
    monkeypatch.setattr(routes.assistant_service.memory, "respond", respond)
    monkeypatch.setattr(routes.assistant_service.tts, "synthesize", synthesize)

    response = create_client().post(
        "/v1/voice/assistant",
        data={"language": "vi"},
        files={"file": ("speech.wav", b"audio-bytes", "audio/wav")},
    )

    assert response.status_code == 200
    assert response.content == b"wav-bytes"
    assert response.headers["content-type"] == "audio/wav"
    assert calls["asr"] == {"audio": b"audio-bytes", "language": "vi"}
    assert calls["memory"] == {
        "text": "Hôm nay tôi nên làm gì?",
        "user_id": "test-user",
    }
    assert calls["tts"] == {
        "text": "You should review your plan.",
        "voice": "Ngọc Linh",
    }


def test_personalization_routes_return_defaults_and_persist_updates(monkeypatch) -> None:
    monkeypatch.setattr(
        routes.auth_service,
        "get_personalization",
        lambda *_: SimpleNamespace(
            nickname="",
            speaking_style="shortAnswers",
            setup_completed=False,
        ),
    )

    response = create_client().get("/v1/profile/personalization")

    assert response.status_code == 200
    assert response.json() == {
        "nickname": "",
        "speaking_style": "shortAnswers",
        "setup_completed": False,
    }

    saved: dict[str, object] = {}

    def set_personalization(
        user_id: str,
        *,
        nickname: str,
        speaking_style: str,
    ) -> SimpleNamespace:
        saved.update(
            {
                "user_id": user_id,
                "nickname": nickname,
                "speaking_style": speaking_style,
            }
        )
        return SimpleNamespace(
            nickname=nickname,
            speaking_style=speaking_style,
            setup_completed=False,
        )

    monkeypatch.setattr(routes.auth_service, "set_personalization", set_personalization)

    update_response = create_client().put(
        "/v1/profile/personalization",
        json={"nickname": "  Alex  ", "speaking_style": "professional"},
    )

    assert update_response.status_code == 200
    assert update_response.json() == {
        "nickname": "Alex",
        "speaking_style": "professional",
        "setup_completed": False,
    }
    assert saved == {
        "user_id": "test-user",
        "nickname": "Alex",
        "speaking_style": "professional",
    }


def test_personalization_route_rejects_invalid_speaking_style() -> None:
    response = create_client().put(
        "/v1/profile/personalization",
        json={"nickname": "Alex", "speaking_style": "verbose"},
    )

    assert response.status_code == 422


def test_profile_setup_route_persists_completion(monkeypatch) -> None:
    saved: dict[str, object] = {}

    def set_setup_completed(user_id: str, completed: bool) -> bool:
        saved["user_id"] = user_id
        saved["completed"] = completed
        return completed

    monkeypatch.setattr(routes.auth_service, "set_setup_completed", set_setup_completed)
    monkeypatch.setattr(
        routes.auth_service,
        "get_personalization",
        lambda *_: SimpleNamespace(
            nickname="Alex",
            speaking_style="casual",
            setup_completed=True,
        ),
    )

    response = create_client().put(
        "/v1/profile/setup",
        json={"setup_completed": True},
    )

    assert response.status_code == 200
    assert response.json() == {
        "nickname": "Alex",
        "speaking_style": "casual",
        "setup_completed": True,
    }
    assert saved == {"user_id": "test-user", "completed": True}


def test_voice_assistant_rejects_empty_upload() -> None:
    response = create_client().post(
        "/v1/voice/assistant",
        data={"language": "vi"},
        files={"file": ("empty.wav", b"", "audio/wav")},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Uploaded file is empty."}


def test_voice_assistant_requires_authentication() -> None:
    response = create_unauthenticated_client().post(
        "/v1/voice/assistant",
        data={"language": "vi"},
        files={"file": ("speech.wav", b"audio-bytes", "audio/wav")},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or expired credentials."}


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
        return AsrResult(text="Xin chào", language=language or "Vietnamese", model="test")

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

    monkeypatch.setattr(routes.auth_service, "get_voice", lambda *_: "Ngọc Linh")
    monkeypatch.setattr(routes.assistant_service.asr, "transcribe", transcribe)
    monkeypatch.setattr(
        routes.assistant_service.memory,
        "search_memory_results",
        search_memory_results,
    )
    monkeypatch.setattr(
        routes.assistant_service.memory,
        "build_response_messages",
        lambda query, user_id, *, memories, recent_messages=None: build_response_messages(
            query,
            memories,
            recent_messages,
            nickname="Alex",
            speaking_style="casual",
        ),
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
        data={"language": "vi"},
        files={"file": ("speech.wav", b"audio-bytes", "audio/wav")},
    )

    assert response.status_code == 200
    events = [json.loads(line) for line in response.text.strip().splitlines()]
    assert events == [
        {"type": "asr", "text": "Xin chào", "language": "vi", "model": "test"},
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
    assert calls["search"] == {"query": "Xin chào", "user_id": "test-user"}
    stream_call = calls["stream"]
    assert isinstance(stream_call, dict)
    messages = stream_call.pop("messages")
    assert stream_call == {
        "query": "Xin chào",
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
    assert messages[2]["role"] == "system"
    assert messages[3] == {"role": "user", "content": "Xin chào"}
    assert "User nickname: Alex" in messages[1]["content"]
    assert "relaxed, conversational wording" in messages[1]["content"]
    prompt = messages[2]["content"]
    assert "Relevant memories CSV:" in prompt
    assert "memory,created_at,updated_at" in prompt
    assert "User likes short answers." in prompt
    assert "2026-06-25T04:08:26+00:00" in prompt
    assert "memory-id" not in prompt
    assert "0.91" not in prompt
    assert calls["tts"] == {"text": "Hi there.", "voice": "Ngọc Linh"}


def test_voice_assistant_stream_persists_after_done(monkeypatch) -> None:
    persisted: list[dict[str, object]] = []

    def transcribe(audio: bytes, language: str | None) -> AsrResult:
        return AsrResult(text="Nhớ việc này", language="Vietnamese", model="test")

    def stream_response(
        query: str,
        memories: list[MemorySearchResult],
        messages: list[dict[str, str]],
    ):
        yield "Saved."

    def synthesize(text: str, voice: object | None) -> TtsResult:
        assert persisted == []
        return TtsResult(audio=b"wav-chunk", media_type="audio/wav")

    def persist_conversation(
        query: str,
        response_text: str,
        user_id: str,
        recent_messages: list[dict[str, str]] | None = None,
        candidate_memories: list[MemorySearchResult] | None = None,
    ) -> None:
        persisted.append(
            {
                "query": query,
                "response_text": response_text,
                "user_id": user_id,
                "recent_messages": recent_messages or [],
                "candidate_memories": candidate_memories or [],
            }
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
        data={"language": "vi"},
        files={"file": ("speech.wav", b"audio-bytes", "audio/wav")},
    )

    assert response.status_code == 200
    assert json.loads(response.text.strip().splitlines()[-1]) == {
        "type": "done",
        "text": "Saved.",
    }
    assert persisted == [
        {
            "query": "Nhớ việc này",
            "response_text": "Saved.",
            "user_id": "test-user",
            "recent_messages": [],
            "candidate_memories": [],
        }
    ]


def test_voice_assistant_stream_records_pipeline_telemetry(monkeypatch) -> None:
    def transcribe(audio: bytes, language: str | None) -> AsrResult:
        return AsrResult(text="Nhớ việc này", language="Vietnamese", model="test")

    def stream_response(
        query: str,
        memories: list[MemorySearchResult],
        messages: list[dict[str, str]],
    ):
        yield "Saved."

    def synthesize(text: str, voice: object | None) -> TtsResult:
        return TtsResult(audio=b"wav-chunk", media_type="audio/wav")

    monkeypatch.setattr(routes.auth_service, "get_voice", lambda *_: "Ngọc Linh")
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
        data={"language": "vi"},
        files={"file": ("speech.wav", b"audio-bytes", "audio/wav")},
    )

    assert response.status_code == 200

    snapshot = assistant_telemetry.snapshot()
    assert snapshot["summary"] == {"active_count": 0, "recent_count": 1}

    run = snapshot["recent_runs"][0]
    stages = {stage["name"]: stage for stage in run["stages"]}
    assert run["status"] == "done"
    assert run["metadata"]["tts_voice"] == "Ngọc Linh"
    assert stages["asr"]["metadata"]["transcript"] == "Nhớ việc này"
    assert stages["memory_search"]["metadata"]["memory_count"] == 1
    assert stages["memory_search"]["metadata"]["memories"] == [
        {
            "id": "memory-id",
            "memory": "User likes concise answers.",
            "score": 0.82,
            "category": "custom_notes",
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
    assert llm_metadata["prompt_messages"][2]["role"] == "system"
    assert llm_metadata["prompt_messages"][3] == {
        "role": "user",
        "content": "Nhớ việc này",
    }
    prompt = llm_metadata["prompt_messages"][2]["content"]
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
    assert stages["tts_synthesis"]["metadata"]["voice"] == "Ngọc Linh"
    tts_chunks = stages["tts_synthesis"]["metadata"]["chunks"]
    assert len(tts_chunks) == 1
    assert tts_chunks[0]["sequence"] == 0
    assert tts_chunks[0]["text"] == "Saved."
    assert tts_chunks[0]["status"] == "streamed"
    assert isinstance(tts_chunks[0]["duration_ms"], int | float)
    assert tts_chunks[0]["duration_ms"] >= 0
    assert stages["mem0_persist_background"]["metadata"] == {
        "persisted": True,
        "candidate_memory_count": 1,
    }


def test_voice_assistant_stream_records_memory_persist_actions(monkeypatch) -> None:
    def transcribe(audio: bytes, language: str | None) -> AsrResult:
        return AsrResult(text="Nhớ việc này", language="Vietnamese", model="test")

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
            MemoryAction(
                event="UPDATE",
                id="memory-id",
                memory="Nguyên nợ tôi năm mươi ngàn.",
                previous_memory="Nguyên nợ tôi tiền.",
            ),
            MemoryAction(
                event="NONE",
                id="1",
                memory="Đang dự định in lại tài liệu",
            ),
        ],
        action_counts={"UPDATE": 1, "NONE": 1},
        raw_result=None,
    )

    monkeypatch.setattr(routes.auth_service, "get_voice", lambda *_: "Ngọc Linh")
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
        data={"language": "vi"},
        files={"file": ("speech.wav", b"audio-bytes", "audio/wav")},
    )

    assert response.status_code == 200

    snapshot = assistant_telemetry.snapshot()
    run = snapshot["recent_runs"][0]
    stages = {stage["name"]: stage for stage in run["stages"]}
    persist_metadata = stages["mem0_persist_background"]["metadata"]

    assert persist_metadata["persisted"] is True
    assert persist_metadata["action_counts"] == {"UPDATE": 1, "NONE": 1}
    assert persist_metadata["memory_actions"] == [
        action.to_dict() for action in persist_result.actions
    ]


def test_get_voice_settings_returns_selected_default_and_available_voices(
    monkeypatch,
) -> None:
    monkeypatch.setattr(routes.auth_service, "get_voice", lambda *_: "Ngọc Linh")
    monkeypatch.setattr(
        routes.tts_service,
        "list_voice_options",
        lambda: [
            TtsVoiceOption(
                id="Ngọc Linh",
                name="Ngọc Linh",
                description="nữ, giọng tươi sáng",
            ),
            TtsVoiceOption(
                id="Mỹ Duyên",
                name="Mỹ Duyên",
                description="nữ, giọng nhẹ nhàng",
            ),
        ],
    )

    response = create_client().get("/v1/voice/settings")

    assert response.status_code == 200
    assert response.json() == {
        "selected_voice": "Ngọc Linh",
        "default_voice": routes.config.tts.default_voice,
        "voices": [
            {
                "id": "Ngọc Linh",
                "name": "Ngọc Linh",
                "description": "nữ, giọng tươi sáng",
            },
            {
                "id": "Mỹ Duyên",
                "name": "Mỹ Duyên",
                "description": "nữ, giọng nhẹ nhàng",
            },
        ],
    }


def test_put_voice_settings_persists_selected_voice(monkeypatch) -> None:
    calls: dict[str, object] = {}

    def set_voice(user_id: str, voice: str) -> str:
        calls["set_voice"] = {"user_id": user_id, "voice": voice}
        return voice

    monkeypatch.setattr(routes.auth_service, "set_voice", set_voice)
    monkeypatch.setattr(
        routes.tts_service,
        "list_voice_options",
        lambda: [
            TtsVoiceOption(
                id="Ngọc Linh",
                name="Ngọc Linh",
                description="nữ, giọng tươi sáng",
            )
        ],
    )

    response = create_client().put(
        "/v1/voice/settings",
        json={"selected_voice": "Ngọc Linh"},
    )

    assert response.status_code == 200
    assert calls["set_voice"] == {
        "user_id": "test-user",
        "voice": "Ngọc Linh",
    }
    assert response.json()["selected_voice"] == "Ngọc Linh"


@pytest.mark.parametrize(
    ("method", "path", "kwargs"),
    [
        ("get", "/v1/memories", {}),
        ("get", "/v1/voice/settings", {}),
        (
            "post",
            "/v1/memories",
            {"json": {"memory": "Test memory.", "category": "goals"}},
        ),
        (
            "patch",
            "/v1/memories/memory-id",
            {"json": {"memory": "Updated memory.", "category": "work"}},
        ),
        ("delete", "/v1/memories/memory-id", {}),
        (
            "put",
            "/v1/memories/settings",
            {"json": {"memory_enabled": False}},
        ),
        (
            "put",
            "/v1/voice/settings",
            {"json": {"selected_voice": "Ngọc Linh"}},
        ),
    ],
)
def test_memory_routes_require_authentication(
    method: str,
    path: str,
    kwargs: dict[str, object],
) -> None:
    response = getattr(create_unauthenticated_client(), method)(path, **kwargs)

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or expired credentials."}


def test_memory_crud_routes_use_authenticated_user(monkeypatch) -> None:
    calls: dict[str, object] = {}

    def list_memories(user_id: str):
        calls["list"] = user_id
        return [
            SimpleNamespace(
                id="memory-id",
                memory="User likes tea.",
                category="preferences",
                created_at="2026-06-25T04:08:26+00:00",
                updated_at="2026-06-25T05:40:29+00:00",
            )
        ]

    def create_memory(user_id: str, memory: str, category: str):
        calls["create"] = {
            "user_id": user_id,
            "memory": memory,
            "category": category,
        }
        return SimpleNamespace(
            id="created-id",
            memory=memory,
            category=category,
            created_at="2026-06-25T04:08:26+00:00",
            updated_at="2026-06-25T05:40:29+00:00",
        )

    def update_memory(user_id: str, memory_id: str, memory: str, category: str):
        calls["update"] = {
            "user_id": user_id,
            "memory_id": memory_id,
            "memory": memory,
            "category": category,
        }
        return SimpleNamespace(
            id=memory_id,
            memory=memory,
            category=category,
            created_at="2026-06-25T04:08:26+00:00",
            updated_at="2026-06-26T05:40:29+00:00",
        )

    def delete_memory(user_id: str, memory_id: str) -> None:
        calls["delete"] = {"user_id": user_id, "memory_id": memory_id}

    monkeypatch.setattr(routes.memory_service, "list_memories", list_memories)
    monkeypatch.setattr(routes.memory_service, "create_memory", create_memory)
    monkeypatch.setattr(routes.memory_service, "update_memory", update_memory)
    monkeypatch.setattr(routes.memory_service, "delete_memory", delete_memory)
    monkeypatch.setattr(routes.memory_service, "is_enabled", lambda user_id: False)

    client = create_client()

    response = client.get("/v1/memories")
    assert response.status_code == 200
    assert response.json() == {
        "memory_enabled": False,
        "memories": [
            {
                "id": "memory-id",
                "memory": "User likes tea.",
                "category": "preferences",
                "created_at": "2026-06-25T04:08:26+00:00",
                "updated_at": "2026-06-25T05:40:29+00:00",
            }
        ],
    }

    response = client.post(
        "/v1/memories",
        json={"memory": "Plan a trip.", "category": "goals"},
    )
    assert response.status_code == 200
    assert response.json()["category"] == "goals"

    response = client.patch(
        "/v1/memories/memory-id",
        json={"memory": "Updated plan.", "category": "work"},
    )
    assert response.status_code == 200
    assert response.json()["updated_at"] == "2026-06-26T05:40:29+00:00"

    response = client.delete("/v1/memories/memory-id")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

    assert calls == {
        "list": "test-user",
        "create": {
            "user_id": "test-user",
            "memory": "Plan a trip.",
            "category": "goals",
        },
        "update": {
            "user_id": "test-user",
            "memory_id": "memory-id",
            "memory": "Updated plan.",
            "category": "work",
        },
        "delete": {"user_id": "test-user", "memory_id": "memory-id"},
    }


def test_memory_settings_route_disables_assistant_memory_runtime(monkeypatch) -> None:
    state = {"enabled": True, "search_calls": 0, "persist_calls": 0}

    def set_enabled(user_id: str, enabled: bool) -> bool:
        state["enabled"] = enabled
        return enabled

    def is_enabled(user_id: str) -> bool:
        return bool(state["enabled"])

    def transcribe(audio: bytes, language: str | None) -> AsrResult:
        return AsrResult(text="Nhớ việc này", language="Vietnamese", model="test")

    def search_memory_results(query: str, user_id: str) -> list[MemorySearchResult]:
        state["search_calls"] += 1
        return []

    def stream_response(
        query: str,
        memories: list[MemorySearchResult],
        messages: list[dict[str, str]],
    ):
        yield "Saved."

    def persist_conversation(*args, **kwargs) -> None:
        state["persist_calls"] += 1

    def synthesize(text: str, voice: object | None) -> TtsResult:
        return TtsResult(audio=b"wav-chunk", media_type="audio/wav")

    monkeypatch.setattr(routes.memory_service, "set_enabled", set_enabled)
    monkeypatch.setattr(routes.assistant_service.memory, "is_enabled", is_enabled)
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
        persist_conversation,
    )
    monkeypatch.setattr(routes.assistant_service.tts, "synthesize", synthesize)

    client = create_client()

    response = client.put("/v1/memories/settings", json={"memory_enabled": False})
    assert response.status_code == 200
    assert response.json() == {"memory_enabled": False}

    response = client.post(
        "/v1/voice/assistant/stream",
        data={"language": "vi"},
        files={"file": ("speech.wav", b"audio-bytes", "audio/wav")},
    )
    assert response.status_code == 200

    assert state["search_calls"] == 0
    assert state["persist_calls"] == 0

    run = assistant_telemetry.snapshot()["recent_runs"][0]
    stages = {stage["name"]: stage for stage in run["stages"]}
    assert stages["memory_search"]["status"] == "skipped"
    assert stages["memory_search"]["metadata"] == {
        "memory_count": 0,
        "memories": [],
        "skip_reason": "memory_disabled",
    }
    assert stages["mem0_persist_background"]["status"] == "skipped"
    assert stages["mem0_persist_background"]["metadata"] == {
        "persisted": False,
        "skip_reason": "memory_disabled",
    }


def test_voice_assistant_telemetry_stream_returns_sse_event() -> None:
    response = routes.voice_assistant_telemetry_stream("test-user")
    assert response.media_type == "text/event-stream"
    assert response.headers["cache-control"] == "no-cache"
    assert response.headers["x-accel-buffering"] == "no"

    event = telemetry_sse_event(with_service_metadata(assistant_telemetry.snapshot()))
    lines = event.splitlines()
    assert lines[0] == "event: telemetry"
    data_line = lines[1]
    assert data_line.startswith("data: ")
    payload = json.loads(data_line.removeprefix("data: "))
    assert payload["summary"] == {"active_count": 0, "recent_count": 0}
    assert payload["services"]["llm_model"] == "deepseek-v4-flash"
    assert payload["services"]["llm_thinking"] == "disabled"


def test_voice_assistant_telemetry_stream_uses_short_keepalive(monkeypatch) -> None:
    calls: dict[str, object] = {}

    def subscribe(keepalive_seconds: float = 15.0, user_id: str | None = None):
        calls["keepalive_seconds"] = keepalive_seconds
        calls["user_id"] = user_id
        yield assistant_telemetry.snapshot()

    monkeypatch.setattr(routes.assistant_telemetry, "subscribe", subscribe)

    response = create_client().get("/v1/voice/assistant/telemetry/stream")

    assert response.status_code == 200
    assert calls == {"keepalive_seconds": 1.0, "user_id": "test-user"}


def test_voice_assistant_telemetry_stream_requires_authentication(monkeypatch) -> None:
    monkeypatch.setattr(
        routes,
        "config",
        SimpleNamespace(telemetry=SimpleNamespace(public_stream="disabled")),
    )
    response = create_unauthenticated_client().get(
        "/v1/voice/assistant/telemetry/stream"
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or expired credentials."}


def test_voice_assistant_telemetry_stream_can_be_public(monkeypatch) -> None:
    monkeypatch.setattr(
        routes,
        "config",
        SimpleNamespace(telemetry=SimpleNamespace(public_stream="enabled")),
    )
    calls: dict[str, object] = {}

    def subscribe(keepalive_seconds: float = 15.0, user_id: str | None = None):
        calls["keepalive_seconds"] = keepalive_seconds
        calls["user_id"] = user_id
        yield assistant_telemetry.snapshot()

    monkeypatch.setattr(routes.assistant_telemetry, "subscribe", subscribe)

    assert routes.telemetry_user_id(None) is None
    response = create_unauthenticated_client().get(
        "/v1/voice/assistant/telemetry/stream"
    )

    assert response.status_code == 200
    payload = json.loads(response.text.splitlines()[1].removeprefix("data: "))
    assert payload["summary"] == {"active_count": 0, "recent_count": 0}
    assert calls == {"keepalive_seconds": 1.0, "user_id": None}


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
