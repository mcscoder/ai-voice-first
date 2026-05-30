from __future__ import annotations

import pytest


@pytest.mark.anyio
async def test_tts_defaults_to_vietnamese(monkeypatch, client):
    calls = []

    async def fake_synthesize_speech(text: str, language: str) -> bytes:
        calls.append((text, language))
        return b"fake-mp3"

    monkeypatch.setattr(
        "text_to_speech_routes.synthesize_speech",
        fake_synthesize_speech,
    )

    response = await client.post("/tts", json={"text": " Xin chao "})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("audio/mpeg")
    assert response.headers["content-disposition"] == (
        'attachment; filename="speech.mp3"'
    )
    assert response.content == b"fake-mp3"
    assert calls == [("Xin chao", "vi")]


@pytest.mark.anyio
async def test_tts_accepts_english_language(monkeypatch, client):
    calls = []

    async def fake_synthesize_speech(text: str, language: str) -> bytes:
        calls.append((text, language))
        return b"fake-mp3"

    monkeypatch.setattr(
        "text_to_speech_routes.synthesize_speech",
        fake_synthesize_speech,
    )

    response = await client.post("/tts", json={"text": "Hello", "language": "en"})

    assert response.status_code == 200
    assert response.content == b"fake-mp3"
    assert calls == [("Hello", "en")]


@pytest.mark.anyio
async def test_openapi_documents_tts_as_binary_audio(client):
    response = await client.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()["paths"]["/tts"]["post"]["responses"]["200"]
    audio_schema = schema["content"]["audio/mpeg"]["schema"]
    assert audio_schema == {"type": "string", "format": "binary"}


@pytest.mark.anyio
async def test_tts_rejects_unsupported_language(client):
    response = await client.post("/tts", json={"text": "Hello", "language": "fr"})

    assert response.status_code == 422


@pytest.mark.anyio
async def test_tts_rejects_missing_text(client):
    response = await client.post("/tts", json={"language": "vi"})

    assert response.status_code == 422


@pytest.mark.anyio
async def test_tts_rejects_whitespace_only_text(client):
    response = await client.post("/tts", json={"text": "   "})

    assert response.status_code == 422
    assert "Text must not be empty" in response.text


@pytest.mark.anyio
async def test_tts_rejects_empty_text(client):
    response = await client.post("/tts", json={"text": ""})

    assert response.status_code == 422
    assert "Text must not be empty" in response.text


@pytest.mark.anyio
async def test_tts_rejects_oversized_text(client):
    response = await client.post("/tts", json={"text": "x" * 5001})

    assert response.status_code == 422
    assert "Text must be at most 5000 characters" in response.text


@pytest.mark.anyio
async def test_tts_allows_max_length_text_after_trimming(monkeypatch, client):
    calls = []

    async def fake_synthesize_speech(text: str, language: str) -> bytes:
        calls.append((len(text), language))
        return b"fake-mp3"

    monkeypatch.setattr(
        "text_to_speech_routes.synthesize_speech",
        fake_synthesize_speech,
    )

    response = await client.post("/tts", json={"text": f" {'x' * 5000} "})

    assert response.status_code == 200
    assert response.content == b"fake-mp3"
    assert calls == [(5000, "vi")]


@pytest.mark.anyio
async def test_tts_returns_bad_gateway_when_service_returns_no_audio(
    monkeypatch,
    client,
):
    from text_to_speech_service import TextToSpeechNoAudioError

    async def fake_synthesize_speech(text: str, language: str) -> bytes:
        raise TextToSpeechNoAudioError("no audio")

    monkeypatch.setattr(
        "text_to_speech_routes.synthesize_speech",
        fake_synthesize_speech,
    )

    response = await client.post("/tts", json={"text": "Xin chao"})

    assert response.status_code == 502
    assert response.json() == {
        "detail": "Text-to-speech service returned no audio.",
    }
