from __future__ import annotations

import os

import pytest
from httpx import ASGITransport, AsyncClient


os.environ["ASR_LOAD_ON_STARTUP"] = "false"
os.environ["TTS_LOAD_ON_STARTUP"] = "false"
os.environ["ASSISTANT_STORE_MEMORIES"] = "false"
os.environ["ASSISTANT_USE_MEMORY_CONTEXT"] = "false"
os.environ["ASSISTANT_PROMPT_LOG_FILE"] = ""

from main import app  # noqa: E402


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest.fixture
async def http_client():
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
