from __future__ import annotations

import threading
from dataclasses import dataclass
from io import BytesIO
from typing import TYPE_CHECKING

import soundfile as sf
from app.core.config import TtsDevice, TtsEmotion, TtsVoice, config
from vieneu import Vieneu
from vieneu.base import BaseVieneuTTS

if TYPE_CHECKING:
    import numpy as np


class TtsError(Exception):
    pass


class EmptyTtsAudioError(TtsError):
    pass


@dataclass(frozen=True)
class TtsResult:
    audio: bytes
    media_type: str


class TtsService:
    """Small wrapper around VieNeu TTS synthesis."""

    def __init__(
        self,
        device: TtsDevice = config.tts.device,
        default_voice: TtsVoice = config.tts.default_voice,
        emotion: TtsEmotion = config.tts.emotion,
    ) -> None:
        self.device = device
        self.default_voice = default_voice
        self.emotion = emotion

        self._model: BaseVieneuTTS | None = None
        self._lock = threading.RLock()

    def load_model(self) -> BaseVieneuTTS:
        with self._lock:
            if self._model is None:
                self._model = Vieneu(
                    device=self.device,
                )
            return self._model

    def synthesize(self, text: str, voice: TtsVoice | None = None) -> TtsResult:
        with self._lock:
            model = self._model or self.load_model()
            voice_data = model.get_preset_voice(voice or self.default_voice)
            audio = model.infer(text=text, voice=voice_data, emotion=self.emotion)
            audio_bytes = self.encode_audio(audio)

        if not audio_bytes:
            raise EmptyTtsAudioError("TTS synthesis returned no audio.")

        return TtsResult(
            audio=audio_bytes,
            media_type="audio/wav",
        )

    def encode_audio(self, audio: np.ndarray) -> bytes:
        model = self._model or self.load_model()
        audio_file = BytesIO()
        sf.write(audio_file, audio, model.sample_rate, format="WAV")
        return audio_file.getvalue()


tts_service = TtsService()
