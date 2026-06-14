from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ServerSettings:
    host: str = "0.0.0.0"
    port: int = 8000


@dataclass(frozen=True, slots=True)
class StartupSettings:
    load_asr_on_startup: bool = True
    load_tts_on_startup: bool = True


@dataclass(frozen=True, slots=True)
class AsrSettings:
    precision: str = "fp32"
    num_threads: int = 4
    provider: str = "cuda"


@dataclass(frozen=True, slots=True)
class Mem0Settings:
    top_k: int = 5
    config: dict = field(
        default_factory=lambda: {
            "llm": {
                "provider": "gemini",
                "config": {
                    "model": "gemini-2.5-flash-lite",
                    "api_key": "suka-blyat",
                },
            },
            "embedder": {
                "provider": "huggingface",
                "config": {
                    "model": "Qwen/Qwen3-Embedding-0.6B",
                    "embedding_dims": 1024,
                },
            },
            "vector_store": {
                "provider": "qdrant",
                "config": {
                    "collection_name": "ai-voice-first",
                    "embedding_model_dims": 1024,
                    "path": ".data/mem0/qdrant",
                    "on_disk": True,
                },
            },
            "history_db_path": ".data/mem0/history.db",
        }
    )


@dataclass(frozen=True, slots=True)
class Settings:
    server: ServerSettings = ServerSettings()
    startup: StartupSettings = StartupSettings()
    asr: AsrSettings = AsrSettings()
    mem0: Mem0Settings = Mem0Settings()


settings = Settings()
