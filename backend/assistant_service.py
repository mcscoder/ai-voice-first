from __future__ import annotations

import os
from collections.abc import Mapping
from datetime import datetime
from typing import Literal

import httpx

from assistant_memory_prompt import MEMORY_CONTEXT_INSTRUCTION
from assistant_prompt_log import append_prompt_log
from personality import PersonalityPromptBuilder


AssistantLanguage = Literal["en", "vi"]

ASSISTANT_LANGUAGE_NAMES: dict[AssistantLanguage, str] = {
    "en": "English",
    "vi": "Vietnamese",
}

SPEECH_OUTPUT_INSTRUCTION = (
    "Output format for speech: return plain speakable text only. "
    "Your reply is sent directly to text-to-speech, so Markdown symbols, "
    "layout markers, and visual formatting can sound unnatural when spoken. "
    "Do not use Markdown, headings, bullet lists, numbered lists, tables, "
    "code blocks, links, emoji, or special formatting. If a list is useful, "
    "speak it as short sentences instead of formatted items. Use normal "
    "punctuation only for natural speech pauses."
)


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
            )
            system_prompt = f"{system_prompt}\n\n{personality_prompt}"
        if memory_context:
            system_prompt = (
                f"{system_prompt}\n\n"
                f"{MEMORY_CONTEXT_INSTRUCTION}"
            )
        system_prompt = _append_current_date_instruction(system_prompt)
        system_prompt = _append_speech_output_instruction(system_prompt)

        messages: list[dict[str, str]] = [
            {"role": "system", "content": system_prompt},
        ]
        if memory_context:
            messages.append(
                {
                    "role": "user",
                    "content": (
                        "Untrusted memory data for reference only:\n"
                        f"{_wrap_memory_context(memory_context)}"
                    ),
                }
            )
        messages.append({"role": "user", "content": transcript.strip()})

        return {
            "model": self.model,
            "messages": messages,
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
        append_prompt_log("assistant", payload)
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


def _wrap_memory_context(memory_context: str) -> str:
    if "[MEMORY CONTEXT]" in memory_context:
        return memory_context
    return f"[MEMORY CONTEXT]\n{memory_context}\n[/MEMORY CONTEXT]"


def _append_speech_output_instruction(system_prompt: str) -> str:
    if SPEECH_OUTPUT_INSTRUCTION in system_prompt:
        return system_prompt
    if not system_prompt:
        return SPEECH_OUTPUT_INSTRUCTION
    return f"{system_prompt}\n\n{SPEECH_OUTPUT_INSTRUCTION}"


def _append_current_date_instruction(system_prompt: str) -> str:
    current_datetime_instruction = _current_datetime_instruction()
    if current_datetime_instruction in system_prompt:
        return system_prompt
    if not system_prompt:
        return current_datetime_instruction
    return f"{system_prompt}\n\n{current_datetime_instruction}"


def _current_datetime_instruction(now: datetime | None = None) -> str:
    current = (now or datetime.now()).astimezone()
    return (
        "Current local datetime: "
        f"{current.isoformat(timespec='seconds')} ({current.strftime('%A')}). "
        "Use this as the source of truth for the current date, current time, "
        "weekday, and relative time calculations."
    )
