from __future__ import annotations

import asyncio

import pytest
from edge_tts.exceptions import NoAudioReceived

import text_to_speech_service


@pytest.mark.anyio
async def test_synthesize_speech_times_out(monkeypatch):
    class HangingCommunicate:
        def __init__(self, text: str, voice: str):
            self.text = text
            self.voice = voice

        async def stream(self):
            await asyncio.sleep(10)
            if False:
                yield {}

    monkeypatch.setattr(text_to_speech_service, "SYNTHESIS_TIMEOUT_SECONDS", 0.01)
    monkeypatch.setattr(
        text_to_speech_service.edge_tts,
        "Communicate",
        HangingCommunicate,
    )

    with pytest.raises(TimeoutError):
        await text_to_speech_service.synthesize_speech("Hello", "en-US-AriaNeural")


@pytest.mark.anyio
async def test_synthesize_speech_rejects_stream_without_audio(monkeypatch):
    class TextOnlyCommunicate:
        def __init__(self, text: str, voice: str):
            self.text = text
            self.voice = voice

        async def stream(self):
            yield {"type": "WordBoundary", "data": b""}

    monkeypatch.setattr(
        text_to_speech_service.edge_tts,
        "Communicate",
        TextOnlyCommunicate,
    )

    with pytest.raises(RuntimeError, match="No audio generated"):
        await text_to_speech_service.synthesize_speech("Hello", "en-US-AriaNeural")


@pytest.mark.anyio
async def test_synthesize_speech_with_fallback_tries_next_voice(monkeypatch):
    calls = []

    async def fake_synthesize_speech(text: str, voice: str) -> bytes:
        calls.append((text, voice))
        if voice == "vi-VN-HoaiMyNeural":
            raise NoAudioReceived("No audio was received")
        return b"fallback-mp3"

    monkeypatch.setattr(
        text_to_speech_service,
        "synthesize_speech",
        fake_synthesize_speech,
    )

    audio = await text_to_speech_service.synthesize_speech_with_fallback(
        "xin chào, hôm nay bạn khỏe không?",
        ("vi-VN-HoaiMyNeural", "vi-VN-NamMinhNeural"),
    )

    assert audio == b"fallback-mp3"
    assert calls == [
        ("xin chào, hôm nay bạn khỏe không?", "vi-VN-HoaiMyNeural"),
        ("xin chào, hôm nay bạn khỏe không?", "vi-VN-NamMinhNeural"),
    ]


@pytest.mark.anyio
async def test_synthesize_speech_with_fallback_rejects_all_no_audio(monkeypatch):
    async def fake_synthesize_speech(text: str, voice: str) -> bytes:
        raise NoAudioReceived("No audio was received")

    monkeypatch.setattr(
        text_to_speech_service,
        "synthesize_speech",
        fake_synthesize_speech,
    )

    with pytest.raises(
        text_to_speech_service.TextToSpeechNoAudioError,
        match="returned no audio",
    ):
        await text_to_speech_service.synthesize_speech_with_fallback(
            "Xin chao",
            ("vi-VN-HoaiMyNeural", "vi-VN-NamMinhNeural"),
        )
