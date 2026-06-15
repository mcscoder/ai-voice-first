from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.services.asr import AsrService, asr_service
from app.services.memory import DEFAULT_USER_ID, MemoryService, memory_service
from app.services.tts import TtsService, tts_service

if TYPE_CHECKING:
    from qwen_asr.inference.utils import AudioLike


@dataclass(frozen=True)
class AssistantResult:
    audio: bytes
    media_type: str


class AssistantService:
    """Coordinates voice assistant ASR, memory, and TTS services."""

    def __init__(
        self,
        asr: AsrService = asr_service,
        memory: MemoryService = memory_service,
        tts: TtsService = tts_service,
        user_id: str = DEFAULT_USER_ID,
    ) -> None:
        self.asr = asr
        self.memory = memory
        self.tts = tts
        self.user_id = user_id

    def respond(
        self,
        audio: bytes | AudioLike,
        language: str | None = None,
    ) -> AssistantResult:
        transcription = self.asr.transcribe(audio, language)
        assistant_reply = self.memory.respond(transcription.text, self.user_id)
        speech = self.tts.synthesize(assistant_reply.text, None)

        return AssistantResult(
            audio=speech.audio,
            media_type=speech.media_type,
        )


assistant_service = AssistantService()
