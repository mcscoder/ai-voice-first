from __future__ import annotations

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from config import settings
from assistant_routes import assistant_service, router as assistant_router
from text_to_speech_routes import router as text_to_speech_router
from text_to_speech_service import load_tts_model, shutdown_tts_model
from transcription_routes import router as transcription_router
from transcription_service import transcription_service


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.startup.load_asr_on_startup:
        transcription_service.load_model()
    if settings.startup.load_tts_on_startup:
        load_tts_model()
    yield
    transcription_service.shutdown_model()
    shutdown_tts_model()


app = FastAPI(title="Voice Assistant API", version="0.1.0", lifespan=lifespan)
app.include_router(assistant_router)
app.include_router(transcription_router)
app.include_router(text_to_speech_router)


def main() -> None:
    uvicorn.run("main:app", host=settings.server.host, port=settings.server.port, reload=False)


if __name__ == "__main__":
    main()
