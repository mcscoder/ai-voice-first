from __future__ import annotations

import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from config import env_flag
from assistant_routes import router as assistant_router
from memory import MemoryService
from text_to_speech_routes import router as text_to_speech_router
from text_to_speech_service import load_tts_model, shutdown_tts_model
from transcription_routes import router as transcription_router
from transcription_service import transcription_service


@asynccontextmanager
async def lifespan(_: FastAPI):
    if env_flag("ASR_LOAD_ON_STARTUP", True):
        transcription_service.load_model()
    if env_flag("TTS_LOAD_ON_STARTUP", True):
        load_tts_model()
    MemoryService().bootstrap()
    yield
    transcription_service.shutdown_model()
    shutdown_tts_model()


app = FastAPI(title="Voice Assistant API", version="0.1.0", lifespan=lifespan)
app.include_router(assistant_router)
app.include_router(transcription_router)
app.include_router(text_to_speech_router)


def main() -> None:
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
