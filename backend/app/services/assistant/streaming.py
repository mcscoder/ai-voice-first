from __future__ import annotations

import base64
import re
from dataclasses import dataclass
from queue import Empty, Full, Queue
from threading import Event, Lock, Thread
from time import perf_counter

from app.services.assistant.telemetry import AssistantTelemetry
from app.services.assistant.types import (
    AssistantMemory,
    AssistantTts,
    ResponseHolder,
    StreamEvent,
)
from app.services.memory.conversation_history import ConversationHistory
from app.services.memory import MemoryServiceError
from app.services.memory.prompt import build_response_messages
from app.services.memory.speech import clean_response_for_speech


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


class AssistantResponseStreamer:
    def __init__(
        self,
        memory: AssistantMemory,
        tts: AssistantTts,
        telemetry: AssistantTelemetry,
        history: ConversationHistory,
    ) -> None:
        self.memory = memory
        self.tts = tts
        self.telemetry = telemetry
        self.history = history

    def stream_response_events(
        self,
        query: str,
        response_holder: ResponseHolder,
        user_id: str,
    ):
        run_id = response_holder.get("run_id")
        memory_enabled = self.memory.is_enabled(user_id)
        response_holder["memory_enabled"] = memory_enabled

        self.telemetry.start_stage(run_id, "memory_search")
        if memory_enabled:
            memory_results = self.memory.search_memory_results(query, user_id)
            self.telemetry.finish_stage(
                run_id,
                "memory_search",
                {
                    "memory_count": len(memory_results),
                    "memories": [item.as_telemetry() for item in memory_results],
                },
            )
        else:
            memory_results = []
            self.telemetry.finish_stage(
                run_id,
                "memory_search",
                {
                    "memory_count": 0,
                    "memories": [],
                    "skip_reason": "memory_disabled",
                },
                status="skipped",
            )

        recent_messages = self.history.messages_for(user_id)
        response_holder["recent_messages"] = recent_messages
        response_holder["candidate_memories"] = memory_results
        prompt_messages = build_response_messages(
            query,
            memory_results,
            recent_messages,
        )
        self.telemetry.start_stage(run_id, "llm_response_stream")
        self.telemetry.update_stage(
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
            self.telemetry.update_stage(
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

                final_text = clean_response_for_speech(full_text)
                if not final_text:
                    raise MemoryServiceError("Memory service returned an empty response.")

                response_holder["text"] = final_text
                self.telemetry.finish_stage_with_duration(
                    run_id,
                    "llm_response_stream",
                    llm_duration_ms,
                    {
                        "characters": len(final_text),
                        "reply_preview": final_text[-240:],
                        "reply_chunks": [dict(chunk) for chunk in reply_chunks],
                    },
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
                        self.telemetry.finish_stage_with_duration(
                            run_id,
                            "tts_synthesis",
                            tts_duration_ms,
                            {"chunk_count": chunk_count},
                        )
                        queue_audio_item(_QueuedStreamComplete(job.final_text))
                        return

                    if job.sequence == 0:
                        self.telemetry.start_stage(run_id, "tts_synthesis")
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
                    # Prefer ready audio briefly so speech can keep up with text without reordering.
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
            # Closing the client stream should stop both background workers promptly.
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
        self.telemetry.update_stage(
            run_id,
            "tts_synthesis",
            {
                "chunk_count": len(chunks),
                "last_chunk_text": last_chunk["text"] if last_chunk else "",
                "current_chunk": dict(current_chunk) if current_chunk else None,
                "chunks": [dict(chunk) for chunk in chunks],
            },
        )

    def _split_tts_chunk(self, text: str) -> tuple[str | None, str]:
        max_chars = 180
        min_chars = 30

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
