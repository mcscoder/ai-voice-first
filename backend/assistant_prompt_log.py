from __future__ import annotations

import json
import os
import re
from collections.abc import Mapping
from datetime import datetime, timezone

from assistant_memory_prompt import MEMORY_CONTEXT_INSTRUCTION


def append_prompt_log(source: str, payload: Mapping[str, object]) -> None:
    path = os.getenv("ASSISTANT_PROMPT_LOG_FILE", "assistant_prompt.log").strip()
    if not path:
        return

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "payload": _redact_prompt_payload(source, payload),
    }
    try:
        with open(path, "a", encoding="utf-8") as file:
            file.write(json.dumps(record, ensure_ascii=False))
            file.write("\n")
    except OSError:
        return


def _redact_prompt_payload(source: str, payload: Mapping[str, object]) -> object:
    if source == "memory_extractor":
        return "[MEMORY EXTRACTION PAYLOAD REDACTED]"
    return _redact_memory_context(payload)


def _redact_memory_context(payload: Mapping[str, object]) -> object:
    return _redact_value(dict(payload))


def _redact_value(value: object) -> object:
    if isinstance(value, str):
        return _redact_memory_text(value)
    if isinstance(value, list):
        return [_redact_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _redact_value(item) for key, item in value.items()}
    return value


def _redact_memory_text(text: str) -> str:
    redacted = re.sub(
        r"\[MEMORY CONTEXT\].*?\[/MEMORY CONTEXT\]",
        "[MEMORY CONTEXT REDACTED]",
        text,
        flags=re.DOTALL,
    )
    if "Relevant memory context:" not in redacted:
        return redacted
    prefix, _, suffix = redacted.partition("Relevant memory context:")
    _, _, after_instruction = suffix.partition(MEMORY_CONTEXT_INSTRUCTION)
    return (
        f"{prefix}Relevant memory context:\n"
        "[MEMORY CONTEXT REDACTED]\n\n"
        f"{MEMORY_CONTEXT_INSTRUCTION}{after_instruction}"
    )
