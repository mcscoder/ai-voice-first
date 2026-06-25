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
from app.services.assistant.telemetry import assistant_telemetry

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
        run_id = assistant_telemetry.start_run(language)
        response_holder["run_id"] = run_id

        try:
            step_start = perf_counter()
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
            assistant_telemetry.start_stage(run_id, "client_stream_done")
            assistant_telemetry.finish_stage(
                run_id,
                "client_stream_done",
                {"completed": True},
            )
        except (AsrError, MemoryServiceError, TtsError) as error:
            assistant_telemetry.fail_run(run_id, str(error))
            yield {"type": "error", "message": str(error)}

    def stream_response_events(
        self,
        query: str,
        response_holder: dict[str, str],
    ) -> Iterator[StreamEvent]:
        run_id = response_holder.get("run_id")
        step_start = perf_counter()
        assistant_telemetry.start_stage(run_id, "memory_search")
        memory_results = self.memory.search_memory_results(query, self.user_id)
        assistant_telemetry.finish_stage(
            run_id,
            "memory_search",
            {
                "memory_count": len(memory_results),
                "memories": [item.as_telemetry() for item in memory_results],
            },
        )
        logger.info(
            "voice_assistant_stream step=memory_search duration_ms=%.2f",
            (perf_counter() - step_start) * 1000,
        )

        prompt_messages = self.memory.build_response_messages(query, memory_results)
        step_start = perf_counter()
        assistant_telemetry.start_stage(run_id, "llm_response_stream")
        assistant_telemetry.update_stage(
            run_id,
            "llm_response_stream",
            {"prompt_messages": prompt_messages},
        )
        sequence = 0
        pending_tts = ""
        full_text = ""
        llm_duration_ms = 0.0
        tts_duration_ms = 0.0
        stream = iter(
            self.memory.stream_response(query, memory_results, prompt_messages)
        )
        while True:
            delta_start = perf_counter()
            try:
                delta = next(stream)
            except StopIteration:
                llm_duration_ms += (perf_counter() - delta_start) * 1000
                break
            llm_duration_ms += (perf_counter() - delta_start) * 1000
            if not delta:
                continue

            full_text = f"{full_text}{delta}"
            response_holder["text"] = full_text
            pending_tts = f"{pending_tts}{delta}"
            assistant_telemetry.update_stage(
                run_id,
                "llm_response_stream",
                {
                    "characters": len(full_text),
                    "reply_preview": full_text[-240:],
                },
            )
            yield {"type": "text_delta", "text": delta}

            sentence, pending_tts = self._split_tts_chunk(pending_tts)
            if sentence is not None:
                if sequence == 0:
                    assistant_telemetry.start_stage(run_id, "tts_synthesis")
                audio_start = perf_counter()
                yield self._audio_event(sentence, sequence)
                tts_duration_ms += (perf_counter() - audio_start) * 1000
                sequence += 1
                assistant_telemetry.update_stage(
                    run_id,
                    "tts_synthesis",
                    {
                        "chunk_count": sequence,
                        "last_chunk_text": sentence,
                    },
                )

        final_chunk = pending_tts.strip()
        if final_chunk:
            if sequence == 0:
                assistant_telemetry.start_stage(run_id, "tts_synthesis")
            audio_start = perf_counter()
            yield self._audio_event(final_chunk, sequence)
            tts_duration_ms += (perf_counter() - audio_start) * 1000
            sequence += 1
            assistant_telemetry.update_stage(
                run_id,
                "tts_synthesis",
                {
                    "chunk_count": sequence,
                    "last_chunk_text": final_chunk,
                },
            )

        final_text = self.memory._clean_response_for_speech(full_text)
        if not final_text:
            raise MemoryServiceError("Memory service returned an empty response.")

        response_holder["text"] = final_text
        response_holder["completed"] = "true"
        assistant_telemetry.finish_stage_with_duration(
            run_id,
            "llm_response_stream",
            llm_duration_ms,
            {
                "characters": len(final_text),
                "reply_preview": final_text[-240:],
            },
        )
        assistant_telemetry.finish_stage_with_duration(
            run_id,
            "tts_synthesis",
            tts_duration_ms,
            {"chunk_count": sequence},
        )
        logger.info(
            "voice_assistant_stream step=llm_response_stream duration_ms=%.2f",
            llm_duration_ms,
        )
        logger.info(
            "voice_assistant_stream step=tts_synthesis duration_ms=%.2f",
            tts_duration_ms,
        )
        logger.info(
            "voice_assistant_stream step=response_and_tts duration_ms=%.2f",
            (perf_counter() - step_start) * 1000,
        )
        yield {"type": "done", "text": final_text}

    def persist_streamed_response(self, response_holder: dict[str, str]) -> None:
        query = response_holder.get("query", "").strip()
        response_text = response_holder.get("text", "").strip()
        run_id = response_holder.get("run_id")
        if response_holder.get("completed") == "true" and query and response_text:
            assistant_telemetry.start_stage(run_id, "mem0_persist_background")
            persist_result = self.memory.persist_conversation(
                query,
                response_text,
                self.user_id,
            )
            persist_metadata: dict[str, object] = {"persisted": True}
            if persist_result is not None:
                persist_metadata.update(
                    {
                        "memory_actions": persist_result.actions,
                        "action_counts": persist_result.action_counts,
                    }
                )
            assistant_telemetry.finish_stage(
                run_id,
                "mem0_persist_background",
                persist_metadata,
            )
            assistant_telemetry.complete_run(run_id)

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
