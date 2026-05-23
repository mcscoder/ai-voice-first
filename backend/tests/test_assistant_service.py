from __future__ import annotations

import json

import httpx
import pytest

from assistant_service import (
    AssistantEmptyReplyError,
    AssistantServiceError,
    AssistantTimeoutError,
    VoiceAssistantService,
)


@pytest.mark.anyio
async def test_complete_builds_prompt_and_extracts_reply():
    requests = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        payload = json.loads(request.content.decode())
        assert payload["model"] == "gemini-2.5-flash-lite"
        assert payload["messages"][0]["role"] == "system"
        assert payload["messages"][1]["content"] == "xin chào"

        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "Xin chào, tôi có thể giúp gì cho bạn?",
                        }
                    }
                ]
            },
            request=request,
        )

    service = VoiceAssistantService(
        base_url="http://assistant.local/v1",
        api_key="secret",
        transport=httpx.MockTransport(handler),
    )

    reply = await service.complete("xin chào", "vi")

    assert reply == "Xin chào, tôi có thể giúp gì cho bạn?"
    assert len(requests) == 1
    assert requests[0].headers["authorization"] == "Bearer secret"
    assert requests[0].url.path == "/v1/chat/completions"


@pytest.mark.anyio
async def test_complete_raises_for_empty_reply():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"choices": [{"message": {"role": "assistant", "content": "   "}}]},
            request=request,
        )

    service = VoiceAssistantService(
        base_url="http://assistant.local/v1",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(AssistantEmptyReplyError):
        await service.complete("xin chào", "vi")


@pytest.mark.anyio
async def test_complete_maps_http_errors_to_service_error():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"detail": "boom"}, request=request)

    service = VoiceAssistantService(
        base_url="http://assistant.local/v1",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(AssistantServiceError):
        await service.complete("xin chào", "vi")


@pytest.mark.anyio
async def test_complete_raises_timeout_error():
    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out", request=request)

    service = VoiceAssistantService(
        base_url="http://assistant.local/v1",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(AssistantTimeoutError):
        await service.complete("xin chào", "vi")
