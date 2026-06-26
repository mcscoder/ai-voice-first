import os
from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path
from typing import Literal

from transformers import BitsAndBytesConfig

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

QuantizationLevel = Literal["none", "int8", "int4-nf4", "int4-fp4"]
DeepSeekThinking = Literal["enabled", "disabled"]
TelemetryPublicStream = Literal["enabled", "disabled"]


def _deepseek_thinking_from_env() -> DeepSeekThinking:
    value = os.getenv("DEEPSEEK_THINKING", "disabled").strip().lower()
    if value not in ("enabled", "disabled"):
        raise ValueError("DEEPSEEK_THINKING must be 'enabled' or 'disabled'.")
    return value


def _telemetry_public_stream_from_env() -> TelemetryPublicStream:
    value = os.getenv("TELEMETRY_PUBLIC_STREAM", "enabled").strip().lower()
    if value not in ("enabled", "disabled"):
        raise ValueError("TELEMETRY_PUBLIC_STREAM must be 'enabled' or 'disabled'.")
    return value


@dataclass(frozen=True)
class QuantizationConfig:
    """Model loading quantization settings for Transformer-backed models."""

    level: QuantizationLevel

    def to_bitsandbytes_config(self) -> BitsAndBytesConfig | None:
        if self.level == "none":
            return None
        if self.level == "int8":
            return BitsAndBytesConfig(load_in_8bit=True)
        if self.level not in ("int4-nf4", "int4-fp4"):
            raise ValueError(f"Unsupported quantization level: {self.level}")

        quant_type = self.level.removeprefix("int4-")
        return BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype="float16",
            bnb_4bit_quant_type=quant_type,
        )

    def to_transformers_kwargs(self) -> dict[str, BitsAndBytesConfig]:
        quantization_config = self.to_bitsandbytes_config()
        if quantization_config is None:
            return {}
        return {"quantization_config": quantization_config}


@dataclass(frozen=True)
class AsrConfig:
    """Runtime settings for automatic speech recognition."""

    model_name: str = "Qwen/Qwen3-ASR-0.6B"
    device: AsrDevice = "auto"
    quantization_level: QuantizationLevel = "int8"
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

    llm_provider: str = "deepseek"
    llm_model: str = "deepseek-v4-flash"
    llm_api_key: str | None = None
    llm_base_url: str = "https://api.deepseek.com/beta"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 2000
    llm_thinking: DeepSeekThinking = field(
        default_factory=_deepseek_thinking_from_env,
    )

    embedder_provider: str = "huggingface"
    embedder_model: str = "Qwen/Qwen3-Embedding-0.6B"
    embedding_dims: int = 1024
    embedding_quantization_level: QuantizationLevel = "int8"

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
                    "deepseek_base_url": self.llm_base_url,
                    "temperature": self.llm_temperature,
                    "max_tokens": self.llm_max_tokens,
                },
            },
            "embedder": {
                "provider": self.embedder_provider,
                "config": {
                    "model": self.embedder_model,
                    "embedding_dims": self.embedding_dims,
                    "model_kwargs": {
                        "model_kwargs": {
                            **QuantizationConfig(
                                self.embedding_quantization_level
                            ).to_transformers_kwargs(),
                            "device_map": "auto",
                        },
                    },
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
            "custom_instructions": (
                "Extract concise, durable memories from Vietnamese voice conversations. "
                "Prefer clear subjects and named people over vague references. "
                "Use recent conversation context only to resolve pronouns or phrases such as "
                "'nó', 'thằng đó', 'người đó', or 'bạn kia'. "
                "Do not store assistant small talk, acknowledgements, or duplicate facts."
            ),
        }

    def to_deepseek_extra_body(self) -> dict[str, object]:
        return {"thinking": {"type": self.llm_thinking}}


@dataclass(frozen=True)
class AuthConfig:
    """Runtime settings for first-party authentication."""

    secret_key: str | None = field(
        default_factory=lambda: os.getenv(
            "AUTH_SECRET_KEY", "replace_with_at_least_32_random_bytes"
        ),
    )
    algorithm: str = "HS256"
    access_token_ttl: timedelta = timedelta(minutes=15)
    refresh_token_ttl: timedelta = timedelta(days=30)
    db_path: Path = Path(__file__).resolve().parents[2] / "data" / "auth.sqlite3"


@dataclass(frozen=True)
class TelemetryConfig:
    """Runtime settings for assistant telemetry diagnostics."""

    public_stream: TelemetryPublicStream = field(
        default_factory=_telemetry_public_stream_from_env,
    )


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
    auth: AuthConfig = field(default_factory=lambda: AuthConfig())
    telemetry: TelemetryConfig = field(default_factory=lambda: TelemetryConfig())


config = AppConfig()
