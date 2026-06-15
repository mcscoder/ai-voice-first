from dataclasses import dataclass, field
from pathlib import Path
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
class MemoryConfig:
    """Runtime settings for Mem0 memory storage."""

    load_on_startup: bool = True

    llm_provider: str = "gemini"
    llm_model: str = "gemini-2.5-flash-lite"
    llm_api_key: str = "suka-blyat"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 2000

    embedder_provider: str = "huggingface"
    embedder_model: str = "Qwen/Qwen3-Embedding-0.6B"
    embedding_dims: int = 1024

    vector_store_provider: str = "qdrant"
    vector_store_collection_name: str = "ai_voice_first_memories"
    data_dir: Path = Path(__file__).resolve().parents[2] / "data" / "mem0"

    @property
    def mem0_dir(self) -> Path:
        return self.data_dir

    @property
    def history_db_path(self) -> str:
        return str(self.data_dir / "history.db")

    @property
    def vector_store_path(self) -> str:
        return str(self.data_dir / "qdrant")

    def to_mem0_config(self) -> dict[str, object]:
        return {
            "llm": {
                "provider": self.llm_provider,
                "config": {
                    "model": self.llm_model,
                    "api_key": self.llm_api_key,
                    "temperature": self.llm_temperature,
                    "max_tokens": self.llm_max_tokens,
                },
            },
            "embedder": {
                "provider": self.embedder_provider,
                "config": {
                    "model": self.embedder_model,
                    "embedding_dims": self.embedding_dims,
                },
            },
            "vector_store": {
                "provider": self.vector_store_provider,
                "config": {
                    "collection_name": self.vector_store_collection_name,
                    "embedding_model_dims": self.embedding_dims,
                    "path": self.vector_store_path,
                },
            },
            "history_db_path": self.history_db_path,
        }


@dataclass(frozen=True)
class AppConfig:
    """Runtime settings for the FastAPI service."""

    host: str = "0.0.0.0"
    port: int = 8000
    title: str = "AI Voice First API"
    version: str = "0.1.0"

    asr: AsrConfig = field(default_factory=AsrConfig)
    tts: TtsConfig = field(default_factory=TtsConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)


config = AppConfig()
