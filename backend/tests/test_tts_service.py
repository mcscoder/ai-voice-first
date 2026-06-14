from __future__ import annotations

import pytest

from app.services.tts import EmptyTtsAudioError, TtsService


def test_tts_service_loads_vieneu_default_model(monkeypatch) -> None:
    calls: list[dict[str, object]] = []

    class FakeVieneu:
        def __init__(self, **kwargs: object) -> None:
            calls.append(kwargs)

    monkeypatch.setattr("app.services.tts.service.Vieneu", FakeVieneu)

    service = TtsService(
        device="cpu",
        default_voice="Gia Bảo",
        emotion="storytelling",
    )
    service.load_model()

    assert calls == [{"device": "cpu"}]


def test_tts_service_synthesizes_wav_audio(monkeypatch) -> None:
    class FakeModel:
        sample_rate = 48000

        def get_preset_voice(self, voice_name: str) -> dict[str, str]:
            assert voice_name == "Mỹ Duyên"
            return {"voice": "my-duyen"}

        def infer(
            self,
            text: str,
            voice: dict[str, str] | None,
            emotion: str,
        ) -> str:
            assert text == "Xin chao"
            assert voice == {"voice": "my-duyen"}
            assert emotion == "natural"
            return "audio"

    class FakeSoundFile:
        @staticmethod
        def write(audio_file, audio: str, sample_rate: int, format: str) -> None:
            assert audio == "audio"
            assert sample_rate == 48000
            assert format == "WAV"
            audio_file.write(b"wav-bytes")

    service = TtsService()
    service._model = FakeModel()
    from app.services.tts import service as tts_module

    monkeypatch.setattr(tts_module, "sf", FakeSoundFile)
    result = service.synthesize("Xin chao")

    assert result.audio == b"wav-bytes"
    assert result.media_type == "audio/wav"


def test_tts_service_rejects_empty_audio(monkeypatch) -> None:
    class FakeModel:
        sample_rate = 48000

        def get_preset_voice(self, voice_name: str) -> dict[str, str]:
            return {"voice": "gia-bao"}

        def infer(
            self,
            text: str,
            voice: dict[str, str] | None,
            emotion: str,
        ) -> str:
            return "audio"

    class FakeSoundFile:
        @staticmethod
        def write(audio_file, audio: str, sample_rate: int, format: str) -> None:
            pass

    service = TtsService(default_voice="Gia Bảo", emotion="storytelling")
    service._model = FakeModel()
    from app.services.tts import service as tts_module

    monkeypatch.setattr(tts_module, "sf", FakeSoundFile)
    with pytest.raises(EmptyTtsAudioError):
        service.synthesize("Xin chao")
