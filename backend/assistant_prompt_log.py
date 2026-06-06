from __future__ import annotations

import json
import os
from collections.abc import Mapping
from datetime import datetime, timezone


def append_prompt_log(source: str, payload: Mapping[str, object]) -> None:
    path = os.getenv("ASSISTANT_PROMPT_LOG_FILE", "assistant_prompt.log").strip()
    if not path:
        return

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "payload": dict(payload),
    }
    try:
        with open(path, "a", encoding="utf-8") as file:
            file.write(json.dumps(record, ensure_ascii=False))
            file.write("\n")
    except OSError:
        return
