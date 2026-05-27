from __future__ import annotations

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

    def fake_transcribe(file_path, language):
        calls.append((file_path, language.value))
        return {
            "text": "hello",
            "requested_language": language.value,
            "model": "base",
            "language": "en",
            "language_probability": 0.99,
            "duration_seconds": 1.2,
        }

    monkeypatch.setattr("transcription_routes.service.transcribe", fake_transcribe)

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
async def test_lifespan_loads_asr_when_enabled(monkeypatch):
    calls = []

    def fake_load_model():
        calls.append("load")

    monkeypatch.setenv("ASR_LOAD_ON_STARTUP", "true")
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
    monkeypatch.setattr(main.transcription_service, "load_model", fake_load_model)

    async with main.app.router.lifespan_context(main.app):
        pass

    assert calls == []


@pytest.mark.anyio
async def test_voice_assistant_returns_audio(monkeypatch, client):
    transcribe_calls = []
    reply_calls = []
    synth_calls = []

    def fake_transcribe(file_path, language):
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
        "assistant_routes.synthesize_speech_with_fallback",
        lambda text, voices: _fake_synthesize(text, voices, synth_calls),
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
        (
            "Xin chào, tôi có thể giúp gì cho bạn?",
            ("vi-VN-HoaiMyNeural", "vi-VN-NamMinhNeural"),
        )
    ]


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
    def fake_transcribe(file_path, language):
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
async def test_voice_assistant_maps_assistant_timeout_to_gateway_timeout(
    monkeypatch,
    client,
):
    def fake_transcribe(file_path, language):
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


async def _fake_synthesize(text: str, voices, calls):
    calls.append((text, voices))
    return b"fake-mp3"
