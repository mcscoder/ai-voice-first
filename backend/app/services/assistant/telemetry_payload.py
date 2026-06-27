from __future__ import annotations

import json

from app.core.config import config


def with_service_metadata(snapshot: dict[str, object]) -> dict[str, object]:
    payload = dict(snapshot)
    payload["services"] = {
        "asr_model": config.asr.model_name,
        "asr_device": config.asr.device,
        "asr_quantization": config.asr.quantization_level,
        "llm_provider": config.memory.llm_provider,
        "llm_model": config.memory.llm_model,
        "llm_thinking": config.memory.llm_thinking,
        "embedder_model": config.memory.embedder_model,
        "tts_device": config.tts.device,
        "tts_default_voice": config.tts.default_voice,
    }
    return payload


def telemetry_sse_event(payload: dict[str, object]) -> str:
    return f"event: telemetry\ndata: {json.dumps(payload)}\n\n"
