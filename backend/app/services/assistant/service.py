from __future__ import annotations

import base64
import logging
import re
from dataclasses import dataclass
from collections.abc import Iterator
from time import perf_counter
from typing import TYPE_CHECKING

from app.services.asr import AsrError, AsrService, asr_service
from app.services.memory import (
    DEFAULT_USER_ID,
    MemoryService,
    MemoryServiceError,
    memory_service,
)
from app.services.tts import TtsError, TtsService, tts_service

if TYPE_CHECKING:
    from qwen_asr.inference.utils import AudioLike


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AssistantResult:
    audio: bytes
    media_type: str


StreamEvent = dict[str, object]


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
        total_start = perf_counter()

        step_start = perf_counter()
        transcription = self.asr.transcribe(audio, language)
        logger.info(
            "voice_assistant step=asr duration_ms=%.2f",
            (perf_counter() - step_start) * 1000,
        )

        step_start = perf_counter()
        assistant_reply = self.memory.respond(transcription.text, self.user_id)
        logger.info(
            "voice_assistant step=memory duration_ms=%.2f",
            (perf_counter() - step_start) * 1000,
        )

        step_start = perf_counter()
        speech = self.tts.synthesize(assistant_reply.text, None)
        logger.info(
            "voice_assistant step=tts duration_ms=%.2f",
            (perf_counter() - step_start) * 1000,
        )
        logger.info(
            "voice_assistant step=total duration_ms=%.2f",
            (perf_counter() - total_start) * 1000,
        )

        return AssistantResult(
            audio=speech.audio,
            media_type=speech.media_type,
        )

    def stream_events(
        self,
        audio: bytes | AudioLike,
        language: str | None,
        response_holder: dict[str, str],
    ) -> Iterator[StreamEvent]:
        total_start = perf_counter()

        try:
            step_start = perf_counter()
            transcription = self.asr.transcribe(audio, language)
            response_holder["query"] = transcription.text
            logger.info(
                "voice_assistant_stream step=asr duration_ms=%.2f",
                (perf_counter() - step_start) * 1000,
            )
            yield {
                "type": "asr",
                "text": transcription.text,
                "language": transcription.language,
                "model": transcription.model,
            }

            yield from self.stream_response_events(transcription.text, response_holder)
            logger.info(
                "voice_assistant_stream step=total duration_ms=%.2f",
                (perf_counter() - total_start) * 1000,
            )
        except (AsrError, MemoryServiceError, TtsError) as error:
            yield {"type": "error", "message": str(error)}

    def stream_response_events(
        self,
        query: str,
        response_holder: dict[str, str],
    ) -> Iterator[StreamEvent]:
        step_start = perf_counter()
        memories = self.memory.search_memories(query, self.user_id)
        logger.info(
            "voice_assistant_stream step=memory_search duration_ms=%.2f",
            (perf_counter() - step_start) * 1000,
        )

        step_start = perf_counter()
        sequence = 0
        pending_tts = ""
        full_text = ""
        for delta in self.memory.stream_response(query, memories):
            if not delta:
                continue

            full_text = f"{full_text}{delta}"
            response_holder["text"] = full_text
            pending_tts = f"{pending_tts}{delta}"
            yield {"type": "text_delta", "text": delta}

            sentence, pending_tts = self._split_tts_chunk(pending_tts)
            if sentence is not None:
                yield self._audio_event(sentence, sequence)
                sequence += 1

        final_chunk = pending_tts.strip()
        if final_chunk:
            yield self._audio_event(final_chunk, sequence)

        final_text = self.memory._clean_response_for_speech(full_text)
        if not final_text:
            raise MemoryServiceError("Memory service returned an empty response.")

        response_holder["text"] = final_text
        response_holder["completed"] = "true"
        logger.info(
            "voice_assistant_stream step=response_tts duration_ms=%.2f",
            (perf_counter() - step_start) * 1000,
        )
        yield {"type": "done", "text": final_text}

    def persist_streamed_response(self, response_holder: dict[str, str]) -> None:
        query = response_holder.get("query", "").strip()
        response_text = response_holder.get("text", "").strip()
        if response_holder.get("completed") == "true" and query and response_text:
            self.memory.persist_conversation(query, response_text, self.user_id)

    def _split_tts_chunk(self, text: str) -> tuple[str | None, str]:
        match = re.search(r"^(.+?[.!?。！？])(\s+|$)", text, flags=re.DOTALL)
        if match:
            return match.group(1).strip(), text[match.end() :].lstrip()

        if len(text) >= 180:
            return text.strip(), ""

        return None, text

    def _audio_event(self, text: str, sequence: int) -> StreamEvent:
        speech = self.tts.synthesize(text, None)
        return {
            "type": "audio",
            "sequence": sequence,
            "media_type": speech.media_type,
            "audio": base64.b64encode(speech.audio).decode("ascii"),
        }


assistant_service = AssistantService()
