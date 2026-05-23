from __future__ import annotations

import os
from pathlib import Path

import httpx
import pytest


RUN_LIVE_SMOKE = os.getenv("RUN_LIVE_VOICE_ASSISTANT_SMOKE") == "1"
VOICE_ASSISTANT_BASE_URL = os.getenv("VOICE_ASSISTANT_BASE_URL", "http://127.0.0.1:8000")
VOICE_ASSISTANT_AUDIO = Path(
    os.getenv("VOICE_ASSISTANT_SMOKE_AUDIO", "../TTS-test/tts-curl-test.mp3")
).resolve()


@pytest.mark.anyio
@pytest.mark.skipif(not RUN_LIVE_SMOKE, reason="live voice assistant smoke test disabled")
async def test_live_voice_assistant_endpoint_returns_reply():
    assert VOICE_ASSISTANT_AUDIO.exists(), f"missing audio fixture: {VOICE_ASSISTANT_AUDIO}"

    audio_bytes = VOICE_ASSISTANT_AUDIO.read_bytes()
    assert audio_bytes, f"empty audio fixture: {VOICE_ASSISTANT_AUDIO}"

    async with httpx.AsyncClient(base_url=VOICE_ASSISTANT_BASE_URL, timeout=45.0) as client:
        response = await client.post(
            "/v1/voice/assistant",
            data={"language": "vi"},
            files={"file": (VOICE_ASSISTANT_AUDIO.name, audio_bytes, "audio/mpeg")},
        )

    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("audio/mpeg")
    assert response.content
