from __future__ import annotations

import os
import re
import threading
from dataclasses import dataclass
from collections.abc import Iterator

from app.core.config import MemoryConfig, config
from mem0 import Memory
from openai import OpenAIError


DEFAULT_USER_ID = "default-user"

VOICE_ASSISTANT_SYSTEM_PROMPT = """You generate final text for VieNeu-TTS.
Return only plain speakable text for tts.infer(text=...).
Write mainly in natural Vietnamese unless the user asks otherwise. Keep replies warm, conversational, concise, and easy to say aloud. Use complete sentences, short sentence length, and punctuation for natural pauses.
Do not use markdown, bullets, tables, headings, code blocks, links, citations, emojis, labels, stage directions, or explanations about TTS.
Make all text voice-friendly. Convert numbers, dates, times, currencies, symbols, measurements, and abbreviations into spoken form. Spell English abbreviations when needed, for example API as A P I. Keep English technical terms only when they sound more natural than translating them.
If the user asks for lists, code, links, tables, or dense technical details, summarize them in smooth spoken prose and mention that details can be shown on screen.
You may use VieNeu-TTS emotion tags only when clearly helpful: [cười], [thở dài], [hắng giọng]. Do not use them in normal replies.
Final output must contain only the text to be spoken.
"""


@dataclass(frozen=True)
class MemoryReply:
    text: str
    user_id: str


class MemoryServiceError(Exception):
    pass


class MemoryService:
    """Lazy wrapper around Mem0 memory storage."""

    def __init__(self, memory_config: MemoryConfig = config.memory) -> None:
        self.memory_config = memory_config
        self._memory: Memory | None = None
        self._lock = threading.RLock()

    def load_memory(self) -> Memory:
        with self._lock:
            if self._memory is None:
                self.memory_config.mem0_dir.mkdir(parents=True, exist_ok=True)
                os.environ.setdefault("MEM0_DIR", str(self.memory_config.mem0_dir))

                self._memory = Memory.from_config(self.memory_config.to_mem0_config())
            return self._memory

    def respond(self, text: str, user_id: str = DEFAULT_USER_ID) -> MemoryReply:
        query = text.strip()
        if not query:
            raise MemoryServiceError("Memory service received empty text.")

        memory = self.load_memory()
        memories = self.search_memories(query, user_id)
        response_text = self.generate_response(query, memories)

        self.persist_conversation(query, response_text, user_id)

        return MemoryReply(text=response_text, user_id=user_id)

    def search_memories(self, query: str, user_id: str) -> list[str]:
        memory = self.load_memory()
        return self._search_memories(memory, query, user_id)

    def generate_response(self, query: str, memories: list[str]) -> str:
        memory = self.load_memory()
        return self._generate_response(memory, query, memories)

    def stream_response(self, query: str, memories: list[str]) -> Iterator[str]:
        memory = self.load_memory()
        messages = self._response_messages(query, memories)
        try:
            stream = memory.llm.client.chat.completions.create(
                model=self.memory_config.llm_model,
                messages=messages,
                temperature=self.memory_config.llm_temperature,
                max_tokens=self.memory_config.llm_max_tokens,
                stream=True,
            )

            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield str(delta)
        except OpenAIError as error:
            raise MemoryServiceError(str(error)) from error

    def persist_conversation(
        self,
        query: str,
        response_text: str,
        user_id: str,
    ) -> None:
        memory = self.load_memory()
        memory.add(
            [
                {"role": "user", "content": query},
                {"role": "assistant", "content": response_text},
            ],
            user_id=user_id,
        )

    def _search_memories(
        self,
        memory: Memory,
        query: str,
        user_id: str,
    ) -> list[str]:
        result = memory.search(query, user_id=user_id, limit=5)
        return [
            item["memory"]
            for item in result.get("results", [])
            if isinstance(item, dict) and isinstance(item.get("memory"), str)
        ]

    def _generate_response(
        self,
        memory: Memory,
        query: str,
        memories: list[str],
    ) -> str:
        response = memory.llm.generate_response(self._response_messages(query, memories))

        response_text = str(response).strip()
        response_text = self._clean_response_for_speech(response_text)
        if not response_text:
            raise MemoryServiceError("Memory service returned an empty response.")

        return response_text

    def _response_messages(self, query: str, memories: list[str]) -> list[dict[str, str]]:
        memory_context = "\n".join(f"- {item}" for item in memories)
        if not memory_context:
            memory_context = "No relevant memories yet."

        return [
            {
                "role": "system",
                "content": VOICE_ASSISTANT_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": f"Relevant memories:\n{memory_context}\n\nUser said:\n{query}",
            },
        ]

    def _clean_response_for_speech(self, text: str) -> str:
        spoken_text = text.strip()
        spoken_text = re.sub(r"```[^\n`]*\n?", "", spoken_text)
        spoken_text = spoken_text.replace("```", "")
        spoken_text = re.sub(r"\[([^\]]+)]\([^)]+\)", r"\1", spoken_text)
        spoken_text = re.sub(r"`([^`]+)`", r"\1", spoken_text)
        spoken_text = re.sub(r"(?m)^\s{0,3}#{1,6}\s+", "", spoken_text)
        spoken_text = re.sub(r"(?m)^\s*>\s?", "", spoken_text)
        spoken_text = re.sub(r"(?m)^\s*[-*+]\s+", "", spoken_text)
        spoken_text = re.sub(r"(?m)^\s*\d+[.)]\s+", "", spoken_text)
        spoken_text = re.sub(r"(?m)^\s*-{3,}\s*$", "", spoken_text)
        spoken_text = re.sub(r"([*_~]{1,3})(\S.*?\S|\S)\1", r"\2", spoken_text)
        spoken_text = re.sub(r"[*_~]{2,}", "", spoken_text)
        spoken_text = re.sub(r"[ \t]+", " ", spoken_text)
        spoken_text = re.sub(r"\s*\n+\s*", " ", spoken_text)
        spoken_text = re.sub(r"\s{2,}", " ", spoken_text)
        return spoken_text.strip()


memory_service = MemoryService()
