from __future__ import annotations

from types import SimpleNamespace

import pytest

import assistant_routes
import main


@pytest.mark.anyio
async def test_openapi_registers_transcribe_and_tts_routes(client):
    response = await client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/v1/voice/assistant" in paths
    assert "/transcribe" in paths
    assert "/tts" in paths


@pytest.mark.anyio
async def test_transcribe_rejects_empty_upload_without_loading_model(client):
    response = await client.post(
        "/transcribe",
        data={"language": "auto"},
        files={"file": ("empty.wav", b"", "audio/wav")},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Uploaded file is empty."}


@pytest.mark.anyio
async def test_transcribe_returns_service_result(monkeypatch, client):
    calls = []

    async def fake_transcribe(file_path, language):
        calls.append((file_path, language.value))
        return {
            "text": "hello",
            "requested_language": language.value,
            "model": "base",
            "language": "en",
            "language_probability": 0.99,
            "duration_seconds": 1.2,
        }

    monkeypatch.setattr("transcription_routes.transcription_service.transcribe", fake_transcribe)

    response = await client.post(
        "/transcribe",
        data={"language": "en"},
        files={"file": ("sample.wav", b"audio-bytes", "audio/wav")},
    )

    assert response.status_code == 200
    assert response.json() == {
        "text": "hello",
        "requested_language": "en",
        "model": "base",
        "language": "en",
        "language_probability": 0.99,
        "duration_seconds": 1.2,
        "filename": "sample.wav",
        "content_type": "audio/wav",
    }
    assert len(calls) == 1
    assert calls[0][1] == "en"


@pytest.mark.anyio
async def test_transcribe_maps_audio_decode_error_to_bad_request(monkeypatch, client):
    async def fake_transcribe(file_path, language):
        raise assistant_routes.AudioTranscriptionError(
            "Uploaded audio could not be decoded."
        )

    monkeypatch.setattr("transcription_routes.transcription_service.transcribe", fake_transcribe)

    response = await client.post(
        "/transcribe",
        data={"language": "vi"},
        files={"file": ("android-recording.m4a", b"audio-bytes", "audio/mp4")},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Uploaded audio could not be decoded."}


@pytest.mark.anyio
async def test_transcribe_maps_backend_decode_error_to_server_error(monkeypatch, client):
    async def fake_transcribe(file_path, language):
        raise assistant_routes.BackendTranscriptionError(
            "Compressed audio requires ffmpeg to be installed."
        )

    monkeypatch.setattr("transcription_routes.transcription_service.transcribe", fake_transcribe)

    response = await client.post(
        "/transcribe",
        data={"language": "vi"},
        files={"file": ("android-recording.m4a", b"audio-bytes", "audio/mp4")},
    )

    assert response.status_code == 500
    assert response.json() == {
        "detail": "Compressed audio requires ffmpeg to be installed.",
    }


@pytest.mark.anyio
async def test_lifespan_loads_asr_when_enabled(monkeypatch):
    calls = []

    def fake_load_model():
        calls.append("load")

    monkeypatch.setenv("ASR_LOAD_ON_STARTUP", "true")
    monkeypatch.setenv("TTS_LOAD_ON_STARTUP", "false")
    monkeypatch.setattr(main.transcription_service, "load_model", fake_load_model)

    async with main.app.router.lifespan_context(main.app):
        pass

    assert calls == ["load"]


@pytest.mark.anyio
async def test_lifespan_skips_asr_when_disabled(monkeypatch):
    calls = []

    def fake_load_model():
        calls.append("load")

    monkeypatch.setenv("ASR_LOAD_ON_STARTUP", "false")
    monkeypatch.setenv("TTS_LOAD_ON_STARTUP", "false")
    monkeypatch.setattr(main.transcription_service, "load_model", fake_load_model)

    async with main.app.router.lifespan_context(main.app):
        pass

    assert calls == []


@pytest.mark.anyio
async def test_lifespan_loads_tts_when_enabled(monkeypatch):
    calls = []

    def fake_load_tts_model():
        calls.append("load")

    monkeypatch.setenv("ASR_LOAD_ON_STARTUP", "false")
    monkeypatch.setenv("TTS_LOAD_ON_STARTUP", "true")
    monkeypatch.setattr(main, "load_tts_model", fake_load_tts_model)

    async with main.app.router.lifespan_context(main.app):
        pass

    assert calls == ["load"]


@pytest.mark.anyio
async def test_lifespan_skips_tts_when_disabled(monkeypatch):
    calls = []

    def fake_load_tts_model():
        calls.append("load")

    monkeypatch.setenv("ASR_LOAD_ON_STARTUP", "false")
    monkeypatch.setenv("TTS_LOAD_ON_STARTUP", "false")
    monkeypatch.setattr(main, "load_tts_model", fake_load_tts_model)

    async with main.app.router.lifespan_context(main.app):
        pass

    assert calls == []


@pytest.mark.anyio
async def test_voice_assistant_returns_audio(monkeypatch, client):
    transcribe_calls = []
    reply_calls = []
    synth_calls = []

    async def fake_transcribe(file_path, language):
        transcribe_calls.append((file_path, language.value))
        return {
            "text": "xin chào",
            "requested_language": language.value,
            "model": "base",
            "language": "vi",
            "language_probability": 0.99,
            "duration_seconds": 1.2,
        }

    async def fake_complete(transcript, language, **kwargs):
        reply_calls.append((transcript, language, kwargs))
        return "Xin chào, tôi có thể giúp gì cho bạn?"

    monkeypatch.setattr("assistant_routes.transcription_service.transcribe", fake_transcribe)
    monkeypatch.setattr("assistant_routes.assistant_service.complete", fake_complete)
    monkeypatch.setattr(
        "assistant_routes.synthesize_speech",
        lambda text, language: _fake_synthesize(text, language, synth_calls),
    )

    response = await client.post(
        "/v1/voice/assistant",
        data={"language": "vi"},
        files={"file": ("sample.wav", b"audio-bytes", "audio/wav")},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("audio/mpeg")
    assert response.headers["content-disposition"] == (
        'attachment; filename="assistant-speech.mp3"'
    )
    assert response.content == b"fake-mp3"
    assert len(transcribe_calls) == 1
    assert transcribe_calls[0][1] == "vi"
    assert transcribe_calls[0][0]
    assert reply_calls[0][0] == "xin chào"
    assert reply_calls[0][1] == "vi"
    assert reply_calls[0][2]["personality"] == "serious"
    assert reply_calls[0][2]["memory_context"] is None
    assert synth_calls == [
        ("Xin chào, tôi có thể giúp gì cho bạn?", "vi")
    ]


@pytest.mark.anyio
async def test_voice_assistant_passes_memory_context_when_enabled(monkeypatch, client):
    reply_calls = []
    memory_context = "[MEMORY CONTEXT]\n- Minh nợ tao 60k (finance)\n[/MEMORY CONTEXT]"

    class FakeMemoryService:
        async def build_context(self, user_id, transcript):
            assert user_id == "local-user"
            assert transcript == "Minh nợ bao nhiêu?"
            return memory_context

    async def fake_transcribe(file_path, language):
        return {
            "text": "Minh nợ bao nhiêu?",
            "requested_language": language.value,
            "model": "base",
            "language": "vi",
            "language_probability": 0.99,
            "duration_seconds": 1.2,
        }

    async def fake_complete(transcript, language, **kwargs):
        reply_calls.append((transcript, language, kwargs))
        return "Minh nợ bạn 60k."

    monkeypatch.setenv("ASSISTANT_USE_MEMORY_CONTEXT", "true")
    monkeypatch.setattr("assistant_routes.MemoryService", lambda: FakeMemoryService())
    monkeypatch.setattr("assistant_routes.transcription_service.transcribe", fake_transcribe)
    monkeypatch.setattr("assistant_routes.assistant_service.complete", fake_complete)
    monkeypatch.setattr(
        "assistant_routes.synthesize_speech",
        lambda text, language: _fake_synthesize(text, language, []),
    )

    response = await client.post(
        "/v1/voice/assistant",
        data={"language": "vi"},
        files={"file": ("sample.wav", b"audio-bytes", "audio/wav")},
    )

    assert response.status_code == 200
    assert reply_calls[0][2]["memory_context"] == memory_context


@pytest.mark.anyio
async def test_voice_assistant_ignores_memory_context_failure(monkeypatch, client):
    reply_calls = []

    class FailingMemoryService:
        async def build_context(self, user_id, transcript):
            raise RuntimeError("database unavailable")

    async def fake_complete(transcript, language, **kwargs):
        reply_calls.append((transcript, language, kwargs))
        return "Tôi chưa tìm thấy ghi nhớ phù hợp."

    monkeypatch.setenv("ASSISTANT_USE_MEMORY_CONTEXT", "true")
    monkeypatch.setattr("assistant_routes.MemoryService", lambda: FailingMemoryService())
    _mock_voice_assistant_before_tts(monkeypatch, complete=fake_complete)
    monkeypatch.setattr(
        "assistant_routes.synthesize_speech",
        lambda text, language: _fake_synthesize(text, language, []),
    )

    response = await client.post(
        "/v1/voice/assistant",
        data={"language": "vi"},
        files={"file": ("sample.wav", b"audio-bytes", "audio/wav")},
    )

    assert response.status_code == 200
    assert reply_calls[0][2]["memory_context"] is None


def test_recall_questions_are_not_memory_storage_candidates():
    assert assistant_routes.should_store_memory_transcript("Minh nợ bao nhiêu?") is False
    assert assistant_routes.should_store_memory_transcript("ai nợ tao tiền?") is False
    assert assistant_routes.should_store_memory_transcript("lần cuối gặp Minh khi nào?") is False
    assert assistant_routes.should_store_memory_transcript("Minh nợ tao 60k") is True
    assert assistant_routes.should_store_memory_transcript("mai gặp Minh") is True


def test_memory_access_defaults_to_all_requests(monkeypatch):
    monkeypatch.delenv("ASSISTANT_ALLOW_REMOTE_MEMORY_CONTEXT", raising=False)
    local_request = SimpleNamespace(client=SimpleNamespace(host="127.0.0.1"))
    remote_request = SimpleNamespace(client=SimpleNamespace(host="203.0.113.10"))

    assert assistant_routes.should_use_memory_for_request(local_request) is True
    assert assistant_routes.should_use_memory_for_request(remote_request) is True

    monkeypatch.setenv("ASSISTANT_ALLOW_REMOTE_MEMORY_CONTEXT", "false")
    assert assistant_routes.should_use_memory_for_request(local_request) is True
    assert assistant_routes.should_use_memory_for_request(remote_request) is False


@pytest.mark.anyio
async def test_voice_assistant_does_not_store_recall_question(monkeypatch, client):
    started_threads = []

    class FakeThread:
        def __init__(self, target, args, daemon):
            started_threads.append((target, args, daemon))

        def start(self):
            raise AssertionError("recall question should not start memory storage")

    async def fake_transcribe(file_path, language):
        return {
            "text": "Minh nợ bao nhiêu?",
            "requested_language": language.value,
            "model": "base",
            "language": "vi",
            "language_probability": 0.99,
            "duration_seconds": 1.2,
        }

    async def fake_complete(transcript, language, **kwargs):
        return "Minh nợ bạn 60k."

    monkeypatch.setenv("ASSISTANT_STORE_MEMORIES", "true")
    monkeypatch.setenv("ASSISTANT_USE_MEMORY_CONTEXT", "false")
    monkeypatch.setattr("assistant_routes.threading.Thread", FakeThread)
    monkeypatch.setattr("assistant_routes.transcription_service.transcribe", fake_transcribe)
    monkeypatch.setattr("assistant_routes.assistant_service.complete", fake_complete)
    monkeypatch.setattr(
        "assistant_routes.synthesize_speech",
        lambda text, language: _fake_synthesize(text, language, []),
    )

    response = await client.post(
        "/v1/voice/assistant",
        data={"language": "vi"},
        files={"file": ("sample.wav", b"audio-bytes", "audio/wav")},
    )

    assert response.status_code == 200
    assert started_threads == []


@pytest.mark.anyio
async def test_voice_assistant_rejects_empty_upload(client):
    response = await client.post(
        "/v1/voice/assistant",
        data={"language": "vi"},
        files={"file": ("empty.wav", b"", "audio/wav")},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Uploaded file is empty."}


@pytest.mark.anyio
async def test_voice_assistant_rejects_empty_transcript(monkeypatch, client):
    async def fake_transcribe(file_path, language):
        return {
            "text": "   ",
            "requested_language": language.value,
            "model": "base",
            "language": "vi",
            "language_probability": 0.99,
            "duration_seconds": 1.2,
        }

    monkeypatch.setattr("assistant_routes.transcription_service.transcribe", fake_transcribe)

    response = await client.post(
        "/v1/voice/assistant",
        data={"language": "vi"},
        files={"file": ("sample.wav", b"audio-bytes", "audio/wav")},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "No speech detected."}


@pytest.mark.anyio
async def test_voice_assistant_maps_audio_decode_error_to_bad_request(
    monkeypatch,
    client,
):
    async def fake_transcribe(file_path, language):
        raise assistant_routes.AudioTranscriptionError(
            "Uploaded audio could not be decoded."
        )

    monkeypatch.setattr("assistant_routes.transcription_service.transcribe", fake_transcribe)

    response = await client.post(
        "/v1/voice/assistant",
        data={"language": "vi"},
        files={"file": ("android-recording.m4a", b"audio-bytes", "audio/mp4")},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Uploaded audio could not be decoded."}


@pytest.mark.anyio
async def test_voice_assistant_maps_backend_decode_error_to_server_error(
    monkeypatch,
    client,
):
    async def fake_transcribe(file_path, language):
        raise assistant_routes.BackendTranscriptionError(
            "Compressed audio requires ffmpeg to be installed."
        )

    monkeypatch.setattr("assistant_routes.transcription_service.transcribe", fake_transcribe)

    response = await client.post(
        "/v1/voice/assistant",
        data={"language": "vi"},
        files={"file": ("android-recording.m4a", b"audio-bytes", "audio/mp4")},
    )

    assert response.status_code == 500
    assert response.json() == {
        "detail": "Compressed audio requires ffmpeg to be installed.",
    }


@pytest.mark.anyio
async def test_voice_assistant_maps_assistant_timeout_to_gateway_timeout(
    monkeypatch,
    client,
):
    async def fake_transcribe(file_path, language):
        return {
            "text": "xin chào",
            "requested_language": language.value,
            "model": "base",
            "language": "vi",
            "language_probability": 0.99,
            "duration_seconds": 1.2,
        }

    async def fake_complete(transcript, language, **kwargs):
        raise assistant_routes.AssistantTimeoutError("Assistant request timed out.")

    monkeypatch.setattr("assistant_routes.transcription_service.transcribe", fake_transcribe)
    monkeypatch.setattr("assistant_routes.assistant_service.complete", fake_complete)

    response = await client.post(
        "/v1/voice/assistant",
        data={"language": "vi"},
        files={"file": ("sample.wav", b"audio-bytes", "audio/wav")},
    )

    assert response.status_code == 504
    assert response.json() == {"detail": "Assistant request timed out."}


@pytest.mark.anyio
async def test_voice_assistant_maps_tts_no_audio_to_bad_gateway(
    monkeypatch,
    client,
):
    from text_to_speech_service import TextToSpeechNoAudioError

    _mock_voice_assistant_before_tts(monkeypatch)

    async def fake_synthesize_speech(text, language):
        raise TextToSpeechNoAudioError("no audio")

    monkeypatch.setattr("assistant_routes.synthesize_speech", fake_synthesize_speech)

    response = await client.post(
        "/v1/voice/assistant",
        data={"language": "vi"},
        files={"file": ("sample.wav", b"audio-bytes", "audio/wav")},
    )

    assert response.status_code == 502
    assert response.json() == {
        "detail": "Text-to-speech service returned no audio.",
    }


@pytest.mark.anyio
async def test_voice_assistant_maps_tts_timeout_to_gateway_timeout(
    monkeypatch,
    client,
):
    _mock_voice_assistant_before_tts(monkeypatch)

    async def fake_synthesize_speech(text, language):
        raise TimeoutError("synthesis timed out")

    monkeypatch.setattr("assistant_routes.synthesize_speech", fake_synthesize_speech)

    response = await client.post(
        "/v1/voice/assistant",
        data={"language": "vi"},
        files={"file": ("sample.wav", b"audio-bytes", "audio/wav")},
    )

    assert response.status_code == 504
    assert response.json() == {"detail": "Assistant speech synthesis timed out."}


async def _fake_synthesize(text: str, language: str, calls):
    calls.append((text, language))
    return b"fake-mp3"


def _mock_voice_assistant_before_tts(monkeypatch, *, complete=None):
    async def fake_transcribe(file_path, language):
        return {
            "text": "xin chào",
            "requested_language": language.value,
            "model": "base",
            "language": "vi",
            "language_probability": 0.99,
            "duration_seconds": 1.2,
        }

    async def fake_complete(transcript, language, **kwargs):
        return "Xin chào, tôi có thể giúp gì cho bạn?"

    monkeypatch.setattr("assistant_routes.transcription_service.transcribe", fake_transcribe)
    monkeypatch.setattr("assistant_routes.assistant_service.complete", complete or fake_complete)
