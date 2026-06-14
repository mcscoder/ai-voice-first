import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.core.config import config
from app.services.asr import asr_service
from app.services.tts import tts_service


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Load the ASR model during startup instead of on the first upload.
    if config.asr.load_on_startup:
        await asyncio.to_thread(asr_service.load_model)
    if config.tts.load_on_startup:
        await asyncio.to_thread(tts_service.load_model)

    yield


app = FastAPI(title=config.title, version=config.version, lifespan=lifespan)
app.include_router(router)


def main() -> None:
    import uvicorn

    uvicorn.run(app, host=config.host, port=config.port)


if __name__ == "__main__":
    main()
