import logging

from app.services.asr import AsrResult
from app.services.assistant.service import AssistantService
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
