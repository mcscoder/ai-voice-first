from __future__ import annotations

import ipaddress

from fastapi import Request

from config import env_flag


def should_store_memories() -> bool:
    return env_flag("ASSISTANT_STORE_MEMORIES", True)


def should_use_memory_context() -> bool:
    return env_flag("ASSISTANT_USE_MEMORY_CONTEXT", True)


def should_use_memory_for_request(request: Request) -> bool:
    if env_flag("ASSISTANT_ALLOW_REMOTE_MEMORY_CONTEXT", True):
        return True
    host = request.client.host if request.client else ""
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False
