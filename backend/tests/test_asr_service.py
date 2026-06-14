from __future__ import annotations

import sys
import types

import numpy as np
import pytest

from app.services.asr import AsrService, UnsupportedAsrLanguageError


def test_asr_service_normalizes_supported_languages() -> None:
    service = AsrService()

    assert service.normalize_language("en") == "English"
    assert service.normalize_language("English") == "English"
    assert service.normalize_language("vi") == "Vietnamese"
    assert service.normalize_language("Vietnamese") == "Vietnamese"


def test_asr_service_rejects_unsupported_languages() -> None:
    service = AsrService()

    with pytest.raises(UnsupportedAsrLanguageError) as exc_info:
        service.normalize_language("fr")

    assert str(exc_info.value) == "Unsupported language. Use one of: English, Vietnamese."


def test_asr_service_transcribes_in_memory_audio() -> None:
    class FakeModel:
        def __init__(self) -> None:
            self.audio = None

        def transcribe(self, audio, language):
            self.audio = audio
            return [types.SimpleNamespace(text="hello", language=language)]

    service = AsrService()
    fake_model = FakeModel()
    service._model = fake_model

    waveform = np.asarray([0.0, 0.25, -0.25], dtype=np.float32)
    result = service.transcribe((waveform, 16000), "English")

    assert result.text == "hello"
    assert result.language == "English"
    assert fake_model.audio == (waveform, 16000)


def test_asr_service_decodes_audio_bytes_before_transcribing(monkeypatch) -> None:
    class FakeModel:
        def __init__(self) -> None:
            self.audio = None

        def transcribe(self, audio, language):
            self.audio = audio
            return [types.SimpleNamespace(text="hello", language=language)]

    waveform = np.asarray([0.0, 0.25, -0.25], dtype=np.float32)

    class FakeSoundFile:
        @staticmethod
        def read(audio_file, dtype, always_2d):
            assert audio_file.read() == b"wav-bytes"
            assert dtype == "float32"
            assert always_2d is False
            return waveform, 44100

    monkeypatch.setattr("app.services.asr.service.sf", FakeSoundFile)

    service = AsrService()
    fake_model = FakeModel()
    service._model = fake_model

    result = service.transcribe(b"wav-bytes", "English")

    assert result.text == "hello"
    assert result.language == "English"
    assert fake_model.audio[1] == 44100
    np.testing.assert_array_equal(fake_model.audio[0], waveform)


def test_asr_service_loads_configured_model_with_auto_device(monkeypatch) -> None:
    calls: list[tuple[str, dict[str, object]]] = []

    class FakeQwen3ASRModel:
        @staticmethod
        def from_pretrained(model_name: str, **kwargs: object) -> object:
            calls.append((model_name, kwargs))
            return object()

    fake_module = types.SimpleNamespace(Qwen3ASRModel=FakeQwen3ASRModel)
    monkeypatch.setitem(sys.modules, "qwen_asr", fake_module)

    service = AsrService(model_name="Qwen/Qwen3-ASR-0.6B", device="auto")
    service.load_model()

    assert calls == [("Qwen/Qwen3-ASR-0.6B", {"device_map": "auto"})]
