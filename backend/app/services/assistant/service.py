from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING

from app.core.config import TtsVoice
from app.services.asr import AsrError, AsrService, asr_service
from app.services.assistant.persistence import StreamPersistence
from app.services.assistant.streaming import AssistantResponseStreamer
from app.services.assistant.telemetry import assistant_telemetry
from app.services.assistant.types import AssistantResult, ResponseHolder, StreamEvent
from app.services.memory import (
    ConversationHistory,
    MemoryService,
    MemoryServiceError,
    conversation_history,
    memory_service,
)
from app.services.tts import TtsError, TtsService, tts_service

if TYPE_CHECKING:
    from qwen_asr.inference.utils import AudioLike


class AssistantService:
    """Coordinates voice assistant ASR, memory, and TTS services."""

    def __init__(
        self,
        asr: AsrService = asr_service,
        memory: MemoryService = memory_service,
        tts: TtsService = tts_service,
        history: ConversationHistory = conversation_history,
    ) -> None:
        self.asr = asr
        self.memory = memory
        self.tts = tts
        self.history = history
        self.response_streamer = AssistantResponseStreamer(
            memory=self.memory,
            tts=self.tts,
            telemetry=assistant_telemetry,
            history=self.history,
        )
        self.stream_persistence = StreamPersistence(
            memory=self.memory,
            telemetry=assistant_telemetry,
            history=self.history,
        )

    def respond(
        self,
        audio: bytes | AudioLike,
        language: str | None = None,
        user_id: str = "",
        selected_voice: TtsVoice | None = None,
    ) -> AssistantResult:
        transcription = self.asr.transcribe(audio, language)
        assistant_reply = self.memory.respond(transcription.text, user_id)
        speech = self.tts.synthesize(assistant_reply.text, selected_voice)

        return AssistantResult(
            audio=speech.audio,
            media_type=speech.media_type,
        )

    def stream_events(
        self,
        audio: bytes | AudioLike,
        language: str | None,
        response_holder: ResponseHolder,
        user_id: str,
        selected_voice: TtsVoice | None = None,
    ) -> Iterator[StreamEvent]:
        run_id = assistant_telemetry.start_run(language, user_id, selected_voice)
        response_holder["run_id"] = run_id
        response_holder["user_id"] = user_id

        try:
            assistant_telemetry.start_stage(run_id, "asr")
            transcription = self.asr.transcribe(audio, language)
            response_holder["query"] = transcription.text
            assistant_telemetry.finish_stage(
                run_id,
                "asr",
                {
                    "language": transcription.language,
                    "model": transcription.model,
                    "transcript": transcription.text,
                },
            )
            yield {
                "type": "asr",
                "text": transcription.text,
                "language": transcription.language,
                "model": transcription.model,
            }

            yield from self.response_streamer.stream_response_events(
                transcription.text,
                response_holder,
                user_id,
                selected_voice,
            )
            assistant_telemetry.start_stage(run_id, "client_stream_done")
            assistant_telemetry.finish_stage(
                run_id,
                "client_stream_done",
                {"completed": True},
            )
        except GeneratorExit:
            reason = "client_disconnected"
            response_holder["cancelled"] = "true"
            response_holder["cancel_reason"] = reason
            assistant_telemetry.cancel_run(run_id, reason)
            raise
        except (AsrError, MemoryServiceError, TtsError) as error:
            assistant_telemetry.fail_run(run_id, str(error))
            yield {"type": "error", "message": str(error)}


assistant_service = AssistantService()
