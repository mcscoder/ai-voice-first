from dataclasses import dataclass, field
from typing import Literal


# "auto" lets Transformers choose at runtime; use "cuda:0" to require GPU 0.
AsrDevice = Literal["auto", "cuda:0", "cpu"]


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
class AppConfig:
    """Runtime settings for the FastAPI service."""

    host: str = "0.0.0.0"
    port: int = 8000
    title: str = "AI Voice First API"
    version: str = "0.1.0"

    asr: AsrConfig = field(default_factory=AsrConfig)


config = AppConfig()
