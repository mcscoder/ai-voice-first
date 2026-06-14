from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    """Runtime settings for the FastAPI service."""

    host: str = "0.0.0.0"
    port: int = 8000
    title: str = "AI Voice First API"
    version: str = "0.1.0"


config = AppConfig()
