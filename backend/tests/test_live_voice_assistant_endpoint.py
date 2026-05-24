from __future__ import annotations

import os

import httpx
import pytest
from httpx import ASGITransport

from main import app
from text_to_speech_service import SUPPORTED_LANGUAGE_VOICES, synthesize_speech_with_fallback


RUN_LIVE_VOICE_ENDPOINT = os.getenv("RUN_LIVE_VOICE_ENDPOINT") == "1"


@pytest.mark.anyio
@pytest.mark.skipif(not RUN_LIVE_VOICE_ENDPOINT, reason="live voice endpoint test disabled")
async def test_live_voice_assistant_endpoint_returns_audio():
    input_audio = await synthesize_speech_with_fallback(
        "Hello there, please reply briefly.",
        SUPPORTED_LANGUAGE_VOICES["en"],
    )

    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver", timeout=90.0) as client:
        response = await client.post(
            "/v1/voice/assistant",
            data={"language": "en"},
            files={"file": ("sample.mp3", input_audio, "audio/mpeg")},
        )

    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("audio/mpeg")
    assert response.content
