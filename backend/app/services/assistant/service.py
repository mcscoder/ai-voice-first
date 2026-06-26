from __future__ import annotations

import base64
import logging
import re
from collections.abc import Iterator
from dataclasses import dataclass
from queue import Empty, Full, Queue
from threading import Event, Lock, Thread
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

_TEXT_EVENT_QUEUE_SIZE = 32
_AUDIO_EVENT_QUEUE_SIZE = 8
_TTS_JOB_QUEUE_SIZE = 4
_QUEUE_TIMEOUT_SECONDS = 0.05
_AUDIO_PRIORITY_WAIT_SECONDS = 0.01
_IDLE_WAIT_SECONDS = 0.005


@dataclass(frozen=True)
class _QueuedTextEvent:
    index: int
    event: StreamEvent


@dataclass(frozen=True)
class _QueuedAudioEvent:
    source_text_index: int
    sequence: int
    event: StreamEvent


@dataclass(frozen=True)
class _TtsJob:
    text: str
    sequence: int
    source_text_index: int


@dataclass(frozen=True)
class _TtsComplete:
    final_text: str


@dataclass(frozen=True)
class _QueuedStreamComplete:
    final_text: str


@dataclass(frozen=True)
class _QueuedStreamError:
    error: Exception


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
        except GeneratorExit:
            reason = "client_disconnected"
            response_holder["cancelled"] = "true"
            response_holder["cancel_reason"] = reason
            assistant_telemetry.cancel_run(run_id, reason)
            raise
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
        stop_event = Event()
        text_events: Queue[_QueuedTextEvent | _QueuedStreamError] = Queue(
            maxsize=_TEXT_EVENT_QUEUE_SIZE,
        )
        audio_events: Queue[
            _QueuedAudioEvent | _QueuedStreamComplete | _QueuedStreamError
        ] = Queue(
            maxsize=_AUDIO_EVENT_QUEUE_SIZE,
        )
        tts_jobs: Queue[_TtsJob | _TtsComplete] = Queue(maxsize=_TTS_JOB_QUEUE_SIZE)
        reply_chunks: list[dict[str, object]] = []
        tts_chunks: list[dict[str, object]] = []
        tts_metadata_lock = Lock()

        def update_llm_metadata(
            characters: int,
            reply_preview: str,
        ) -> None:
            assistant_telemetry.update_stage(
                run_id,
                "llm_response_stream",
                {
                    "characters": characters,
                    "reply_preview": reply_preview,
                    "reply_chunks": [dict(chunk) for chunk in reply_chunks],
                },
            )

        def append_tts_chunk(job: _TtsJob) -> None:
            with tts_metadata_lock:
                tts_chunks.append(
                    {
                        "sequence": job.sequence,
                        "text": job.text,
                        "status": "queued",
                    }
                )
                self._publish_tts_metadata(
                    run_id,
                    tts_chunks,
                    current_chunk=None,
                )

        def update_tts_chunk_status(
            sequence: int,
            status: str,
            current_chunk: dict[str, object] | None,
            metadata: dict[str, object] | None = None,
        ) -> None:
            with tts_metadata_lock:
                for chunk in tts_chunks:
                    if chunk["sequence"] == sequence:
                        chunk["status"] = status
                        if metadata:
                            chunk.update(metadata)
                        break
                self._publish_tts_metadata(run_id, tts_chunks, current_chunk)

        def queue_text_item(item: _QueuedTextEvent | _QueuedStreamError) -> bool:
            return self._put_queue(text_events, item, stop_event)

        def queue_audio_item(
            item: _QueuedAudioEvent | _QueuedStreamComplete | _QueuedStreamError,
        ) -> bool:
            return self._put_queue(audio_events, item, stop_event)

        def queue_tts_job(job: _TtsJob | _TtsComplete) -> bool:
            return self._put_queue(tts_jobs, job, stop_event)

        def produce_llm_chunks() -> None:
            sequence = 0
            text_index = 0
            pending_tts = ""
            full_text = ""
            llm_duration_ms = 0.0
            stream = iter(
                self.memory.stream_response(query, memory_results, prompt_messages)
            )
            try:
                while not stop_event.is_set():
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
                    text_index += 1
                    reply_chunks.append({"index": text_index, "text": delta})
                    update_llm_metadata(len(full_text), full_text[-240:])
                    if not queue_text_item(
                        _QueuedTextEvent(
                            text_index,
                            {"type": "text_delta", "text": delta},
                        )
                    ):
                        return

                    sentence, pending_tts = self._split_tts_chunk(pending_tts)
                    if sentence is not None:
                        job = _TtsJob(sentence, sequence, text_index)
                        append_tts_chunk(job)
                        if not queue_tts_job(job):
                            return
                        sequence += 1

                final_chunk = pending_tts.strip()
                if final_chunk:
                    job = _TtsJob(final_chunk, sequence, text_index)
                    append_tts_chunk(job)
                    if not queue_tts_job(job):
                        return
                    sequence += 1

                final_text = self.memory._clean_response_for_speech(full_text)
                if not final_text:
                    raise MemoryServiceError("Memory service returned an empty response.")

                response_holder["text"] = final_text
                assistant_telemetry.finish_stage_with_duration(
                    run_id,
                    "llm_response_stream",
                    llm_duration_ms,
                    {
                        "characters": len(final_text),
                        "reply_preview": final_text[-240:],
                        "reply_chunks": [dict(chunk) for chunk in reply_chunks],
                    },
                )
                logger.info(
                    "voice_assistant_stream step=llm_response_stream duration_ms=%.2f",
                    llm_duration_ms,
                )
                queue_tts_job(_TtsComplete(final_text))
            except Exception as error:
                queue_text_item(_QueuedStreamError(error))
                stop_event.set()

        def synthesize_tts_chunks() -> None:
            chunk_count = 0
            tts_duration_ms = 0.0
            try:
                while not stop_event.is_set():
                    try:
                        job = tts_jobs.get(timeout=_QUEUE_TIMEOUT_SECONDS)
                    except Empty:
                        continue

                    if isinstance(job, _TtsComplete):
                        assistant_telemetry.finish_stage_with_duration(
                            run_id,
                            "tts_synthesis",
                            tts_duration_ms,
                            {"chunk_count": chunk_count},
                        )
                        logger.info(
                            "voice_assistant_stream step=tts_synthesis duration_ms=%.2f",
                            tts_duration_ms,
                        )
                        logger.info(
                            "voice_assistant_stream step=response_and_tts duration_ms=%.2f",
                            (perf_counter() - step_start) * 1000,
                        )
                        queue_audio_item(_QueuedStreamComplete(job.final_text))
                        return

                    if job.sequence == 0:
                        assistant_telemetry.start_stage(run_id, "tts_synthesis")
                    current_chunk = {
                        "sequence": job.sequence,
                        "text": job.text,
                    }
                    update_tts_chunk_status(
                        job.sequence,
                        "synthesizing",
                        current_chunk,
                    )
                    audio_start = perf_counter()
                    event = self._audio_event(job.text, job.sequence)
                    chunk_duration_ms = (perf_counter() - audio_start) * 1000
                    tts_duration_ms += chunk_duration_ms
                    chunk_count += 1
                    update_tts_chunk_status(
                        job.sequence,
                        "synthesized",
                        None,
                        {"duration_ms": chunk_duration_ms},
                    )
                    if not queue_audio_item(
                        _QueuedAudioEvent(job.source_text_index, job.sequence, event)
                    ):
                        return
            except Exception as error:
                queue_audio_item(_QueuedStreamError(error))
                stop_event.set()

        producer = Thread(target=produce_llm_chunks, daemon=True)
        tts_worker = Thread(target=synthesize_tts_chunks, daemon=True)
        producer.start()
        tts_worker.start()

        try:
            yielded_text_index = 0
            pending_audio: list[_QueuedAudioEvent] = []
            final_text: str | None = None
            while True:
                ready_audio = self._pop_ready_audio(
                    pending_audio,
                    yielded_text_index,
                )
                if ready_audio is not None:
                    update_tts_chunk_status(
                        ready_audio.sequence,
                        "streamed",
                        None,
                    )
                    yield ready_audio.event
                    continue

                audio_item = self._get_queue_nowait(audio_events)
                if isinstance(audio_item, _QueuedStreamError):
                    raise audio_item.error
                if isinstance(audio_item, _QueuedStreamComplete):
                    final_text = audio_item.final_text
                    if self._stream_complete(text_events, pending_audio):
                        yield {"type": "done", "text": final_text}
                        response_holder["completed"] = "true"
                        return
                    continue
                if isinstance(audio_item, _QueuedAudioEvent):
                    if audio_item.source_text_index <= yielded_text_index:
                        update_tts_chunk_status(
                            audio_item.sequence,
                            "streamed",
                            None,
                        )
                        yield audio_item.event
                    else:
                        pending_audio.append(audio_item)
                    continue

                if yielded_text_index > 0:
                    audio_item = self._get_queue_wait(
                        audio_events,
                        _AUDIO_PRIORITY_WAIT_SECONDS,
                    )
                    if isinstance(audio_item, _QueuedStreamError):
                        raise audio_item.error
                    if isinstance(audio_item, _QueuedStreamComplete):
                        final_text = audio_item.final_text
                        if self._stream_complete(text_events, pending_audio):
                            yield {"type": "done", "text": final_text}
                            response_holder["completed"] = "true"
                            return
                    elif isinstance(audio_item, _QueuedAudioEvent):
                        if audio_item.source_text_index <= yielded_text_index:
                            update_tts_chunk_status(
                                audio_item.sequence,
                                "streamed",
                                None,
                            )
                            yield audio_item.event
                            continue
                        pending_audio.append(audio_item)

                text_item = self._get_queue_nowait(text_events)
                if isinstance(text_item, _QueuedStreamError):
                    raise text_item.error
                if isinstance(text_item, _QueuedTextEvent):
                    yielded_text_index = text_item.index
                    yield text_item.event
                    continue

                if final_text is not None and self._stream_complete(
                    text_events,
                    pending_audio,
                ):
                    yield {"type": "done", "text": final_text}
                    response_holder["completed"] = "true"
                    return

                if not producer.is_alive() and not tts_worker.is_alive():
                    raise MemoryServiceError(
                        "Assistant stream ended before completion."
                    )

                stop_event.wait(_IDLE_WAIT_SECONDS)
        finally:
            stop_event.set()
            producer.join(timeout=1.0)
            tts_worker.join(timeout=1.0)

    def _put_queue(
        self,
        queue: Queue[object],
        item: object,
        stop_event: Event,
    ) -> bool:
        while not stop_event.is_set():
            try:
                queue.put(item, timeout=_QUEUE_TIMEOUT_SECONDS)
                return True
            except Full:
                continue
        return False

    def _get_queue_nowait(self, queue: Queue[object]) -> object | None:
        try:
            return queue.get_nowait()
        except Empty:
            return None

    def _get_queue_wait(
        self,
        queue: Queue[object],
        timeout_seconds: float,
    ) -> object | None:
        try:
            return queue.get(timeout=timeout_seconds)
        except Empty:
            return None

    def _pop_ready_audio(
        self,
        pending_audio: list[_QueuedAudioEvent],
        yielded_text_index: int,
    ) -> _QueuedAudioEvent | None:
        ready_index = next(
            (
                index
                for index, item in enumerate(pending_audio)
                if item.source_text_index <= yielded_text_index
            ),
            None,
        )
        if ready_index is None:
            return None
        return pending_audio.pop(ready_index)

    def _stream_complete(
        self,
        text_events: Queue[object],
        pending_audio: list[_QueuedAudioEvent],
    ) -> bool:
        return text_events.empty() and not pending_audio

    def _publish_tts_metadata(
        self,
        run_id: str | None,
        chunks: list[dict[str, object]],
        current_chunk: dict[str, object] | None,
    ) -> None:
        last_chunk = chunks[-1] if chunks else None
        assistant_telemetry.update_stage(
            run_id,
            "tts_synthesis",
            {
                "chunk_count": len(chunks),
                "last_chunk_text": last_chunk["text"] if last_chunk else "",
                "current_chunk": dict(current_chunk) if current_chunk else None,
                "chunks": [dict(chunk) for chunk in chunks],
            },
        )

    def persist_streamed_response(self, response_holder: dict[str, str]) -> None:
        query = response_holder.get("query", "").strip()
        response_text = response_holder.get("text", "").strip()
        run_id = response_holder.get("run_id")

        assistant_telemetry.start_stage(run_id, "mem0_persist_background")
        if response_holder.get("completed") != "true" or not query or not response_text:
            assistant_telemetry.finish_stage(
                run_id,
                "mem0_persist_background",
                {
                    "persisted": False,
                    "skip_reason": self._persist_skip_reason(response_holder),
                },
                status="skipped",
            )
            assistant_telemetry.complete_run(run_id)
            return

        persist_result = self.memory.persist_conversation(
            query,
            response_text,
            self.user_id,
        )
        persist_metadata: dict[str, object] = {
            "persisted": True,
        }
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

    def _persist_skip_reason(self, response_holder: dict[str, str]) -> str:
        if response_holder.get("cancelled") == "true":
            return response_holder.get("cancel_reason", "client_disconnected")
        if not response_holder.get("query", "").strip():
            return "missing_query"
        if not response_holder.get("text", "").strip():
            return "missing_response"
        return "stream_not_completed"

    def _split_tts_chunk(self, text: str) -> tuple[str | None, str]:
        max_chars = 180
        min_chars = 40

        for match in re.finditer(r"[.!?。！？,]", text):
            chunk = text[: match.end()].strip()

            if match.group(0) == ",":
                if len(chunk) > 40:
                    return chunk, text[match.end() :].lstrip()
                continue

            if match.end() == len(text) or text[match.end()].isspace():
                return chunk, text[match.end() :].lstrip()

        if len(text) >= max_chars:
            split_at = None

            for match in re.finditer(r"\s+", text[:max_chars]):
                if match.start() >= min_chars:
                    split_at = match.start()

            if split_at is not None:
                return text[:split_at].strip(), text[split_at:].lstrip()

            return None, text

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
