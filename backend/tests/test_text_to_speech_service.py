from __future__ import annotations

import pytest

import text_to_speech_service


@pytest.mark.anyio
async def test_synthesize_speech_rejects_empty_service_audio(monkeypatch):
    class FakeService:
        async def synthesize(self, text):
            raise text_to_speech_service.TextToSpeechNoAudioError("no audio")

    monkeypatch.setattr(text_to_speech_service, "tts_service", FakeService())

    with pytest.raises(
        text_to_speech_service.TextToSpeechNoAudioError,
        match="no audio",
    ):
        await text_to_speech_service.synthesize_speech("Xin chao", "vi")


@pytest.mark.anyio
async def test_synthesize_speech_uses_service(monkeypatch):
    class FakeService:
        def __init__(self):
            self.calls = []

        async def synthesize(self, text):
            self.calls.append(text)
            return b"fake-mp3"

    service = FakeService()
    monkeypatch.setattr(text_to_speech_service, "tts_service", service)

    audio = await text_to_speech_service.synthesize_speech("Xin chao", "vi")

    assert audio == b"fake-mp3"
    assert service.calls == ["Xin chao"]


def test_synthesis_encodes_vieneu_waveform_to_mp3():
    class FakeEngine:
        def infer(self, **kwargs):
            assert kwargs == {"text": "Xin chao", "show_progress": False}
            return [0.0] * 2400

    audio = text_to_speech_service._synthesize_with_engine(FakeEngine(), "Xin chao")

    assert audio.startswith(b"\xff")
    assert len(audio) > 0


def test_load_tts_model_starts_service(monkeypatch):
    class FakeService:
        def __init__(self):
            self.calls = []

        def load_model(self) -> None:
            self.calls.append("load")

    service = FakeService()
    monkeypatch.setattr(text_to_speech_service, "tts_service", service)

    text_to_speech_service.load_tts_model()

    assert service.calls == ["load"]


def test_create_tts_engine_uses_turbo_gpu_cuda(monkeypatch):
    constructor_calls = []

    def fake_vieneu(**kwargs):
        constructor_calls.append(kwargs)
        return object()

    monkeypatch.setattr(text_to_speech_service, "_ensure_cuda_provider_available", lambda: None)
    monkeypatch.setattr("vieneu.Vieneu", fake_vieneu)

    text_to_speech_service._create_tts_engine()

    assert constructor_calls == [
        {
            "mode": "turbo_gpu",
            "backbone_repo": "pnnbao-ump/VieNeu-TTS-v2-Turbo",
            "decoder_repo": "pnnbao-ump/VieNeu-Codec",
            "encoder_repo": "pnnbao-ump/VieNeu-Codec",
            "device": "cuda",
            "backend": "standard",
        }
    ]


def test_cuda_provider_check_rejects_cpu_only_onnxruntime(monkeypatch):
    monkeypatch.setattr(
        "onnxruntime.get_available_providers",
        lambda: ["AzureExecutionProvider", "CPUExecutionProvider"],
    )

    with pytest.raises(RuntimeError, match="CUDAExecutionProvider"):
        text_to_speech_service._ensure_cuda_provider_available()
