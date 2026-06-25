import logging
from threading import Event

from app.services.asr import AsrResult
from app.services.assistant.service import AssistantService
from app.services.assistant.telemetry import assistant_telemetry
from app.services.memory import MemoryReply
from app.services.tts import TtsResult


class StubAsr:
    def transcribe(self, audio: bytes, language: str | None) -> AsrResult:
        return AsrResult(
            text="Remember my meeting",
            language=language or "English",
            model="test",
        )


class StubMemory:
    def respond(self, text: str, user_id: str) -> MemoryReply:
        return MemoryReply(text=f"Stored: {text}", user_id=user_id)


class StubTts:
    def synthesize(self, text: str, voice: object | None) -> TtsResult:
        return TtsResult(audio=b"assistant-audio", media_type="audio/wav")


class StreamingMemory:
    def __init__(self, deltas: list[str] | None = None) -> None:
        self.deltas = deltas or ["One. ", "Two. "]
        self.persisted: list[dict[str, str]] = []

    def search_memory_results(self, query: str, user_id: str) -> list[object]:
        return []

    def build_response_messages(
        self,
        query: str,
        memories: list[object],
    ) -> list[dict[str, str]]:
        return []

    def stream_response(
        self,
        query: str,
        memories: list[object],
        messages: list[dict[str, str]],
    ):
        yield from self.deltas

    def _clean_response_for_speech(self, text: str) -> str:
        return text.strip()

    def persist_conversation(
        self,
        query: str,
        response_text: str,
        user_id: str,
    ) -> None:
        self.persisted.append(
            {
                "query": query,
                "response_text": response_text,
                "user_id": user_id,
            }
        )


class RecordingTts:
    def __init__(self, second_started: Event | None = None) -> None:
        self.started: list[str] = []
        self.second_started = second_started or Event()

    def synthesize(self, text: str, voice: object | None) -> TtsResult:
        self.started.append(text)
        if text == "Two.":
            self.second_started.set()
        return TtsResult(audio=text.encode(), media_type="audio/wav")


class BlockingFirstTts:
    def __init__(
        self,
        release_first_audio: Event,
        first_started: Event | None = None,
    ) -> None:
        self.release_first_audio = release_first_audio
        self.first_started = first_started or Event()

    def synthesize(self, text: str, voice: object | None) -> TtsResult:
        if text == "One.":
            self.first_started.set()
            assert self.release_first_audio.wait(timeout=1.0)
        return TtsResult(audio=text.encode(), media_type="audio/wav")


def test_assistant_logs_step_timings(monkeypatch, caplog) -> None:
    times = iter([1.0, 1.0, 1.1, 1.1, 1.4, 1.4, 1.9, 2.0])
    monkeypatch.setattr(
        "app.services.assistant.service.perf_counter",
        lambda: next(times),
    )

    service = AssistantService(
        asr=StubAsr(),
        memory=StubMemory(),
        tts=StubTts(),
        user_id="test-user",
    )

    with caplog.at_level(logging.INFO, logger="app.services.assistant.service"):
        result = service.respond(b"audio-bytes", "English")

    assert result.audio == b"assistant-audio"
    assert result.media_type == "audio/wav"
    messages = [record.getMessage() for record in caplog.records]
    assert messages == [
        "voice_assistant step=asr duration_ms=100.00",
        "voice_assistant step=memory duration_ms=300.00",
        "voice_assistant step=tts duration_ms=500.00",
        "voice_assistant step=total duration_ms=1000.00",
    ]


def test_stream_response_keeps_synthesizing_after_audio_event_is_yielded() -> None:
    tts = RecordingTts()
    service = AssistantService(
        asr=StubAsr(),
        memory=StreamingMemory(),
        tts=tts,
        user_id="test-user",
    )

    events = service.stream_response_events("Hello", {"run_id": None})
    try:
        while True:
            event = next(events)
            if event["type"] == "audio" and event["sequence"] == 0:
                break

        assert tts.second_started.wait(timeout=1.0)
        assert tts.started == ["One.", "Two."]
    finally:
        events.close()


def test_stream_response_records_current_tts_chunk_while_synthesizing() -> None:
    assistant_telemetry.reset()
    release_first_audio = Event()
    first_started = Event()
    run_id = assistant_telemetry.start_run(None)
    service = AssistantService(
        asr=StubAsr(),
        memory=StreamingMemory(["One. "]),
        tts=BlockingFirstTts(release_first_audio, first_started),
        user_id="test-user",
    )

    events = service.stream_response_events("Hello", {"run_id": run_id})
    try:
        assert next(events) == {"type": "text_delta", "text": "One. "}
        assert first_started.wait(timeout=1.0)

        run = assistant_telemetry.snapshot()["active_runs"][0]
        stages = {stage["name"]: stage for stage in run["stages"]}
        tts_metadata = stages["tts_synthesis"]["metadata"]
        assert tts_metadata["current_chunk"] == {"sequence": 0, "text": "One."}
        assert tts_metadata["chunks"] == [
            {"sequence": 0, "text": "One.", "status": "synthesizing"}
        ]
        assert "duration_ms" not in tts_metadata["chunks"][0]
    finally:
        release_first_audio.set()
        events.close()
        assistant_telemetry.reset()


def test_stream_response_yields_ready_audio_before_later_text() -> None:
    release_first_audio = Event()
    service = AssistantService(
        asr=StubAsr(),
        memory=StreamingMemory(["One. ", "Two. ", "Three. "]),
        tts=BlockingFirstTts(release_first_audio),
        user_id="test-user",
    )

    events = service.stream_response_events("Hello", {"run_id": None})
    try:
        first = next(events)
        assert first == {"type": "text_delta", "text": "One. "}
        release_first_audio.set()

        second = next(events)
        assert second["type"] == "audio"
        assert second["sequence"] == 0
    finally:
        events.close()


def test_cancelled_stream_skips_memory_persist_and_completes_telemetry() -> None:
    assistant_telemetry.reset()
    memory = StreamingMemory(["One. ", "Two. "])
    service = AssistantService(
        asr=StubAsr(),
        memory=memory,
        tts=RecordingTts(),
        user_id="test-user",
    )
    response_holder: dict[str, str] = {}

    events = service.stream_events(b"audio-bytes", None, response_holder)
    assert next(events)["type"] == "asr"
    assert next(events) == {"type": "text_delta", "text": "One. "}
    events.close()

    service.persist_streamed_response(response_holder)

    assert "completed" not in response_holder
    assert response_holder["cancelled"] == "true"
    assert memory.persisted == []

    run = assistant_telemetry.snapshot()["recent_runs"][0]
    stages = {stage["name"]: stage for stage in run["stages"]}
    assert run["status"] == "cancelled"
    assert run["metadata"]["cancel_reason"] == "client_disconnected"
    assert stages["mem0_persist_background"]["status"] == "skipped"
    assert stages["mem0_persist_background"]["metadata"] == {
        "persisted": False,
        "skip_reason": "client_disconnected",
    }
    assistant_telemetry.reset()


def test_stream_closed_after_done_event_does_not_persist() -> None:
    memory = StreamingMemory(["Done. "])
    service = AssistantService(
        asr=StubAsr(),
        memory=memory,
        tts=RecordingTts(),
        user_id="test-user",
    )
    response_holder = {"run_id": None}
    events = service.stream_response_events("Hello", response_holder)

    try:
        event_types = []
        while True:
            event = next(events)
            event_types.append(event["type"])
            if event["type"] == "done":
                break
    finally:
        events.close()

    service.persist_streamed_response(response_holder)

    assert event_types == ["text_delta", "audio", "done"]
    assert "completed" not in response_holder
    assert memory.persisted == []
