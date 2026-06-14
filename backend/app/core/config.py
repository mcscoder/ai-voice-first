from dataclasses import dataclass, field
from typing import Literal


# ASR runs on Qwen/Transformers; use "cuda:0" to require GPU 0.
AsrDevice = Literal["auto", "cuda:0", "cpu"]

# TTS runs on VieNeu; use "cuda" to require CUDA.
TtsDevice = Literal["auto", "cuda", "cpu"]

# VieNeu emotion tags passed to infer().
TtsEmotion = Literal["natural", "storytelling"]

# Built-in VieNeu v3 Turbo preset voices.
TtsVoice = Literal[
    "Ngọc Lan",
    "Gia Bảo",
    "Thái Sơn",
    "Đức Trí",
    "Mỹ Duyên",
    "Trúc Ly",
    "Xuân Vĩnh",
    "Trọng Hữu",
    "Bình An",
    "Ngọc Linh",
]


@dataclass(frozen=True)
class AsrConfig:
    """Runtime settings for automatic speech recognition."""

    model_name: str = "Qwen/Qwen3-ASR-0.6B"
    device: AsrDevice = "auto"
    load_on_startup: bool = True

    default_language: str = "English"
    supported_languages: tuple[str, str] = ("English", "Vietnamese")
    language_map: dict[str, str] = field(
        default_factory=lambda: {
            "en": "English",
            "english": "English",
            "vi": "Vietnamese",
            "vietnamese": "Vietnamese",
        },
    )


@dataclass(frozen=True)
class TtsConfig:
    """Runtime settings for text-to-speech synthesis."""

    device: TtsDevice = "auto"
    load_on_startup: bool = True

    default_voice: TtsVoice = "Mỹ Duyên"
    emotion: TtsEmotion = "natural"
    max_text_length: int = 5000


@dataclass(frozen=True)
class AppConfig:
    """Runtime settings for the FastAPI service."""

    host: str = "0.0.0.0"
    port: int = 8000
    title: str = "AI Voice First API"
    version: str = "0.1.0"

    asr: AsrConfig = field(default_factory=AsrConfig)
    tts: TtsConfig = field(default_factory=TtsConfig)


config = AppConfig()
