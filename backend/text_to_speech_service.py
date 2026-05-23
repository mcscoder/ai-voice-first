from __future__ import annotations

import asyncio
from collections.abc import Sequence

import edge_tts
from edge_tts.exceptions import NoAudioReceived


SYNTHESIS_TIMEOUT_SECONDS = 30
MAX_TEXT_LENGTH = 5000
SUPPORTED_LANGUAGE_VOICES = {
    "vi": ("vi-VN-HoaiMyNeural", "vi-VN-NamMinhNeural"),
    "en": ("en-US-AriaNeural",),
}


class TextToSpeechNoAudioError(Exception):
    pass


async def synthesize_speech(text: str, voice: str) -> bytes:
    audio = bytearray()

    async with asyncio.timeout(SYNTHESIS_TIMEOUT_SECONDS):
        communicate = edge_tts.Communicate(text, voice)
        async for message in communicate.stream():
            if message["type"] == "audio":
                audio.extend(message["data"])

    if not audio:
        raise RuntimeError("No audio generated")

    return bytes(audio)


async def synthesize_speech_with_fallback(text: str, voices: Sequence[str]) -> bytes:
    last_error: Exception | None = None

    for voice in voices:
        try:
            return await synthesize_speech(text, voice)
        except NoAudioReceived as exc:
            last_error = exc

    raise TextToSpeechNoAudioError(
        "The text-to-speech service returned no audio."
    ) from last_error
