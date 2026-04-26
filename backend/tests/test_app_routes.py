from __future__ import annotations

import pytest

import main


@pytest.mark.anyio
async def test_openapi_registers_transcribe_and_tts_routes(client):
    response = await client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
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
async def test_lifespan_loads_whisper_when_enabled(monkeypatch):
    calls = []

    def fake_load_model():
        calls.append("load")

    monkeypatch.setenv("WHISPER_LOAD_ON_STARTUP", "true")
    monkeypatch.setattr(main.transcription_service, "load_model", fake_load_model)

    async with main.app.router.lifespan_context(main.app):
        pass

    assert calls == ["load"]


@pytest.mark.anyio
async def test_lifespan_skips_whisper_when_disabled(monkeypatch):
    calls = []

    def fake_load_model():
        calls.append("load")

    monkeypatch.setenv("WHISPER_LOAD_ON_STARTUP", "false")
    monkeypatch.setattr(main.transcription_service, "load_model", fake_load_model)

    async with main.app.router.lifespan_context(main.app):
        pass

    assert calls == []
