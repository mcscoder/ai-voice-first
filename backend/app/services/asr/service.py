from __future__ import annotations

import threading
from dataclasses import dataclass
from io import BytesIO
from typing import TYPE_CHECKING

import av
import numpy as np
from app.core.config import AsrDevice, config
from qwen_asr import Qwen3ASRModel

if TYPE_CHECKING:
    from qwen_asr.inference.utils import AudioLike


class AsrError(Exception):
    pass


class UnsupportedAsrLanguageError(AsrError):
    pass


@dataclass(frozen=True)
class AsrResult:
    text: str
    language: str
    model: str


class AsrService:
    """Small wrapper around Qwen ASR model loading and transcription."""

    def __init__(
        self,
        model_name: str = config.asr.model_name,
        device: AsrDevice = config.asr.device,
        language_map: dict[str, str] | None = None,
    ) -> None:
        self.model_name = model_name
        self.device = device
        self.language_map = language_map or config.asr.language_map

        self._model: Qwen3ASRModel | None = None
        self._lock = threading.RLock()

    def load_model(self) -> Qwen3ASRModel:
        with self._lock:
            if self._model is None:
                self._model = Qwen3ASRModel.from_pretrained(
                    self.model_name,
                    device_map=self.device,
                )
            return self._model

    def transcribe(
        self,
        audio: bytes | AudioLike,
        language: str | None = None,
    ) -> AsrResult:
        normalized_language = self.normalize_language(language)
        audio_input = (
            self.decode_audio_bytes(audio) if isinstance(audio, bytes) else audio
        )

        with self._lock:
            # Startup normally loads the model, but keep this fallback for direct use.
            model = self._model or self.load_model()
            results = model.transcribe(
                audio=audio_input,
                language=normalized_language,
            )

        if not results:
            raise AsrError("ASR transcription returned no results.")

        result = results[0]
        return AsrResult(
            text=result.text,
            language=result.language or normalized_language,
            model=self.model_name,
        )

    def decode_audio_bytes(self, audio_bytes: bytes) -> AudioLike:
        audio_chunks: list[np.ndarray] = []
        sample_rate: int | None = None

        with av.open(BytesIO(audio_bytes), mode="r") as container:
            for frame in container.decode(audio=0):
                sample_rate = int(frame.sample_rate)
                chunk = frame.to_ndarray()
                audio_chunks.append(self._normalize_audio_chunk(chunk))

        if not audio_chunks or sample_rate is None:
            raise AsrError("Uploaded audio contains no decodable audio frames.")

        audio = np.concatenate(audio_chunks, axis=0)
        if audio.shape[1] == 1:
            audio = audio[:, 0]

        return np.asarray(audio, dtype=np.float32), int(sample_rate)

    def _normalize_audio_chunk(self, chunk: np.ndarray) -> np.ndarray:
        audio = np.asarray(chunk)
        if audio.ndim == 1:
            audio = audio.reshape(-1, 1)
        elif audio.ndim == 2:
            audio = audio.T
        else:
            raise AsrError(f"Unsupported decoded audio shape: {audio.shape}.")

        audio = audio.astype(np.float32)
        if np.issubdtype(chunk.dtype, np.integer):
            max_value = float(np.iinfo(chunk.dtype).max)
            audio = audio / max_value
        return audio

    def normalize_language(self, language: str | None) -> str:
        # Accept API aliases while passing canonical language names to the model.
        key = (language or config.asr.default_language).strip().lower()
        normalized = self.language_map.get(key)

        if normalized is None:
            supported = ", ".join(config.asr.supported_languages)
            raise UnsupportedAsrLanguageError(
                f"Unsupported language. Use one of: {supported}."
            )
        return normalized


asr_service = AsrService()
