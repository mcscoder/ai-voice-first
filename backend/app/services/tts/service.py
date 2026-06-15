from __future__ import annotations

import threading
from dataclasses import dataclass
from io import BytesIO

import av
import numpy as np
from app.core.config import TtsDevice, TtsEmotion, TtsVoice, config
from vieneu import Vieneu
from vieneu.base import BaseVieneuTTS


class TtsError(Exception):
    pass


class EmptyTtsAudioError(TtsError):
    pass


@dataclass(frozen=True)
class TtsResult:
    audio: bytes
    media_type: str


def encode_wav_audio(audio: np.ndarray, sample_rate: int) -> bytes:
    audio_file = BytesIO()
    audio_array = format_audio_frame(audio)
    layout = "mono" if audio_array.shape[0] == 1 else "stereo"

    with av.open(audio_file, mode="w", format="wav") as container:
        stream = container.add_stream("pcm_s16le", rate=sample_rate)
        stream.layout = layout

        frame = av.AudioFrame.from_ndarray(
            audio_array,
            format="flt",
            layout=layout,
        )
        frame.sample_rate = sample_rate

        for packet in stream.encode(frame):
            container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)

    return audio_file.getvalue()


def format_audio_frame(audio: np.ndarray) -> np.ndarray:
    audio_array = np.asarray(audio, dtype=np.float32)
    if audio_array.ndim == 1:
        return audio_array.reshape(1, -1)
    if audio_array.ndim != 2:
        raise TtsError(f"Unsupported TTS audio shape: {audio_array.shape}.")

    if audio_array.shape[0] in (1, 2):
        channels_first = audio_array
    else:
        channels_first = audio_array.T

    if channels_first.shape[0] not in (1, 2):
        raise TtsError("TTS WAV encoding supports mono or stereo audio.")

    return np.ascontiguousarray(channels_first, dtype=np.float32)


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
        return encode_wav_audio(audio, model.sample_rate)


tts_service = TtsService()
