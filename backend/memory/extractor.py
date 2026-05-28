from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from collections.abc import Mapping

import httpx

from .prompts import EXTRACTION_PROMPT
from .schemas import ExtractedEntity, ExtractedFinancial, ExtractedMemory


MEMORY_EXTRACTION_LANGUAGE_MODEL = os.getenv(
    "ASSISTANT_MODEL",
    "gemini-2.5-flash-lite",
)

ALLOWED_CATEGORIES = {"finance", "work", "relationship", "plan", "emotion", "general"}
ALLOWED_ENTITY_TYPES = {"person", "place", "organization"}
ALLOWED_FINANCIAL_TYPES = {"debt_owed", "debt_owed_to", "expense", "income"}


class MemoryExtractionError(Exception):
    pass


class MemoryExtractor:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        timeout_seconds: float | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = (
            base_url
            or os.getenv("ASSISTANT_API_BASE_URL", "http://127.0.0.1:8317/v1")
        ).strip()
        self.api_key = (api_key or os.getenv("ASSISTANT_API_KEY", "")).strip()
        self.model = (model or MEMORY_EXTRACTION_LANGUAGE_MODEL).strip()
        self.timeout_seconds = timeout_seconds or float(
            os.getenv("ASSISTANT_PROVIDER_TIMEOUT_SECONDS", "30")
        )
        self._transport = transport

    def extract(self, raw_text: str) -> ExtractedMemory:
        cleaned_text = " ".join(raw_text.strip().split())
        if not cleaned_text:
            return ExtractedMemory(processed_text="")

        payload = self._build_payload(cleaned_text)
        _append_prompt_log("memory_extractor", payload)
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            with httpx.Client(
                base_url=self.base_url.rstrip("/"),
                timeout=httpx.Timeout(self.timeout_seconds),
                transport=self._transport,
            ) as client:
                response = client.post("/chat/completions", json=payload, headers=headers)
                response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise MemoryExtractionError("Memory extraction timed out.") from exc
        except httpx.HTTPError as exc:
            raise MemoryExtractionError("Memory extraction request failed.") from exc

        content = self._extract_reply(self._safe_json(response))
        if not content:
            raise MemoryExtractionError("Memory extraction returned no content.")

        return ExtractedMemory.model_validate(
            self._normalize_payload(self._parse_content(content), cleaned_text)
        )

    def _build_payload(self, transcript: str) -> dict[str, object]:
        return {
            "model": self.model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": EXTRACTION_PROMPT.strip()},
                {
                    "role": "user",
                    "content": (
                        "Transcript:\n"
                        f"{transcript}\n\n"
                        "Return the JSON object now."
                    ),
                },
            ],
        }

    def _safe_json(self, response: httpx.Response) -> Mapping[str, object]:
        try:
            payload = response.json()
        except ValueError as exc:
            raise MemoryExtractionError("Memory extraction returned invalid JSON.") from exc
        if not isinstance(payload, Mapping):
            raise MemoryExtractionError("Memory extraction returned an invalid payload.")
        return payload

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

    def _parse_content(self, content: str) -> dict[str, object]:
        candidate = self._extract_json_candidate(content)
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError as exc:
            raise MemoryExtractionError("Memory extraction did not return valid JSON.") from exc
        if not isinstance(parsed, dict):
            raise MemoryExtractionError("Memory extraction JSON must be an object.")
        return parsed

    def _extract_json_candidate(self, content: str) -> str:
        fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", content, flags=re.DOTALL)
        if fenced:
            return fenced.group(1).strip()

        start = content.find("{")
        end = content.rfind("}")
        if start >= 0 and end > start:
            return content[start : end + 1].strip()
        return content.strip()

    def _normalize_payload(
        self,
        payload: dict[str, object],
        fallback_text: str,
    ) -> dict[str, object]:
        processed_text = self._coerce_string(payload.get("processed_text")) or fallback_text
        category = self._coerce_string(payload.get("category"), default="general").lower()
        if category not in ALLOWED_CATEGORIES:
            category = "general"

        subcategory = self._coerce_string(payload.get("subcategory"))
        entities = self._normalize_entities(payload.get("entities"))
        financial = self._normalize_financial(payload.get("financial"))
        sentiment = self._clamp_float(payload.get("sentiment"), -1.0, 1.0, default=0.0)
        importance = int(round(self._clamp_float(payload.get("importance"), 1.0, 10.0, default=1.0)))
        emotional_tags = self._normalize_strings(payload.get("emotional_tags"))
        time_references = self._normalize_strings(payload.get("time_references"))

        normalized: dict[str, object] = {
            "processed_text": processed_text,
            "category": category,
            "subcategory": subcategory,
            "entities": entities,
            "financial": financial,
            "sentiment": sentiment,
            "importance": importance,
            "emotional_tags": emotional_tags,
            "time_references": time_references,
        }
        return normalized

    def _normalize_entities(self, value: object) -> list[dict[str, object]]:
        if not isinstance(value, list):
            return []

        entities: list[dict[str, object]] = []
        seen: set[tuple[str, str]] = set()
        for item in value:
            if not isinstance(item, Mapping):
                continue
            name = self._coerce_string(item.get("name"))
            if not name:
                continue
            entity_type = self._coerce_string(item.get("type"), default="person").lower()
            if entity_type not in ALLOWED_ENTITY_TYPES:
                entity_type = "person"
            role = self._coerce_string(item.get("role"), default="mentioned")
            key = (name.lower(), entity_type)
            if key in seen:
                continue
            seen.add(key)
            entities.append(
                ExtractedEntity(name=name, type=entity_type, role=role).model_dump()
            )
        return entities

    def _normalize_financial(self, value: object) -> dict[str, object] | None:
        if value is None:
            return None
        if not isinstance(value, Mapping):
            return None

        amount = self._clamp_float(value.get("amount"), 0.0, 1_000_000_000.0, default=0.0)
        currency = self._coerce_string(value.get("currency"), default="VND")
        financial_type = self._coerce_string(value.get("type"), default="debt_owed").lower()
        if financial_type not in ALLOWED_FINANCIAL_TYPES:
            financial_type = "debt_owed"
        person_name = self._coerce_string(value.get("person_name"))
        due_date = self._coerce_string(value.get("due_date"))
        return ExtractedFinancial(
            amount=amount,
            currency=currency,
            type=financial_type,
            person_name=person_name,
            due_date=due_date,
        ).model_dump()

    def _normalize_strings(self, value: object) -> list[str]:
        if not isinstance(value, list):
            return []
        results: list[str] = []
        for item in value:
            text = self._coerce_string(item)
            if text and text not in results:
                results.append(text)
        return results

    def _coerce_string(self, value: object, default: str | None = None) -> str | None:
        if isinstance(value, str):
            stripped = value.strip()
            if stripped:
                return stripped
        return default

    def _clamp_float(
        self,
        value: object,
        minimum: float,
        maximum: float,
        *,
        default: float,
    ) -> float:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return default
        return max(minimum, min(maximum, number))


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
