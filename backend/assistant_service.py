from __future__ import annotations

import os
import json
from datetime import datetime, timezone
from collections.abc import Mapping
from typing import Literal

import httpx

from personality import PersonalityPromptBuilder


AssistantLanguage = Literal["en", "vi"]

ASSISTANT_LANGUAGE_NAMES: dict[AssistantLanguage, str] = {
    "en": "English",
    "vi": "Vietnamese",
}


class AssistantServiceError(Exception):
    pass


class AssistantTimeoutError(AssistantServiceError):
    pass


class AssistantEmptyReplyError(AssistantServiceError):
    pass


class VoiceAssistantService:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        system_prompt: str | None = None,
        timeout_seconds: float | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = (
            base_url
            or os.getenv("ASSISTANT_API_BASE_URL", "http://127.0.0.1:8317/v1")
        ).strip()
        self.api_key = (api_key or os.getenv("ASSISTANT_API_KEY", "")).strip()
        self.model = (model or os.getenv("ASSISTANT_MODEL", "gemini-2.5-flash-lite")).strip()
        self.system_prompt = (
            system_prompt
            or os.getenv(
                "ASSISTANT_SYSTEM_PROMPT",
                "You are a helpful voice assistant. Reply in {language_name}. "
                "Keep answers concise, natural, and useful. "
                "Do not mention transcripts or internal processing.",
            )
        ).strip()
        self.timeout_seconds = timeout_seconds or float(
            os.getenv("ASSISTANT_PROVIDER_TIMEOUT_SECONDS", "30")
        )
        self._transport = transport
        self._prompt_builder = PersonalityPromptBuilder()

    def build_payload(
        self,
        transcript: str,
        language: AssistantLanguage,
        *,
        memory_context: str | None = None,
        personality: str | None = None,
    ) -> dict[str, object]:
        language_name = ASSISTANT_LANGUAGE_NAMES[language]
        system_prompt = self.system_prompt.replace("{language_name}", language_name)
        if personality:
            personality_prompt = self._prompt_builder.build_system_prompt(
                personality=personality,
                language=language_name,
                memory_context=memory_context,
            )
            system_prompt = f"{system_prompt}\n\n{personality_prompt}"
        elif memory_context:
            system_prompt = f"{system_prompt}\n\nRelevant memory context:\n{memory_context}"

        return {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": transcript.strip()},
            ],
        }

    async def complete(
        self,
        transcript: str,
        language: AssistantLanguage,
        *,
        memory_context: str | None = None,
        personality: str | None = None,
    ) -> str:
        payload = self.build_payload(
            transcript,
            language,
            memory_context=memory_context,
            personality=personality,
        )
        _append_prompt_log("assistant", payload)
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            async with httpx.AsyncClient(
                base_url=self.base_url.rstrip("/"),
                timeout=httpx.Timeout(self.timeout_seconds),
                transport=self._transport,
            ) as client:
                response = await client.post("/chat/completions", json=payload, headers=headers)
                response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise AssistantTimeoutError("Assistant request timed out.") from exc
        except httpx.HTTPError as exc:
            raise AssistantServiceError("Assistant request failed.") from exc

        content = self._extract_reply(response.json())
        if not content:
            raise AssistantEmptyReplyError("Assistant service returned no reply.")

        return content

    def _extract_reply(self, payload: Mapping[str, object]) -> str:
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices:
            return ""

        first_choice = choices[0]
        if not isinstance(first_choice, Mapping):
            return ""

        message = first_choice.get("message")
        if not isinstance(message, Mapping):
            return ""

        content = message.get("content")
        if not isinstance(content, str):
            return ""

        return content.strip()


def _append_prompt_log(source: str, payload: Mapping[str, object]) -> None:
    path = os.getenv("ASSISTANT_PROMPT_LOG_FILE", "assistant_prompt.log").strip()
    if not path:
        return

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "payload": payload,
    }
    try:
        with open(path, "a", encoding="utf-8") as file:
            file.write(json.dumps(record, ensure_ascii=False))
            file.write("\n")
    except OSError:
        return
