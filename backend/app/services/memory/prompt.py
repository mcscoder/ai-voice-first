from __future__ import annotations

import csv
from datetime import datetime, timezone
from io import StringIO

from app.services.memory.types import MemorySearchResult


VOICE_ASSISTANT_SYSTEM_PROMPT = """You generate final text for VieNeu-TTS.
Return only plain speakable text for tts.infer(text=...).
Use plain spoken text only.
Write mainly in natural Vietnamese unless the user asks otherwise. Sound like a real human assistant. Keep replies warm, conversational, concise, and easy to say aloud. Use complete sentences, short sentence length, and punctuation for natural pauses.
Do not use Markdown, bullets, tables, headings, code blocks, links, citations, emojis, labels, stage directions, or explanations about TTS.
Make all text voice-friendly. Convert numbers, dates, times, currencies, symbols, measurements, and abbreviations into spoken form. Spell English abbreviations when needed, for example API as A P I. Keep English technical terms only when they sound more natural than translating them.
If the user asks for lists, code, links, tables, or dense technical details, summarize them in smooth spoken prose and mention that details can be shown on screen.
You may use VieNeu-TTS emotion tags only when clearly helpful: [cười], [thở dài], [hắng giọng]. Do not use them in normal replies.
Final output must contain only the text to be spoken.
"""


def build_response_messages(
    query: str,
    memories: list[MemorySearchResult],
) -> list[dict[str, str]]:
    local_now = datetime.now().astimezone().isoformat()
    utc_now = datetime.now(timezone.utc).isoformat()
    memory_context = format_memory_context_csv(memories)
    if not memory_context:
        memory_context = "No relevant memories yet."

    return [
        {
            "role": "system",
            "content": VOICE_ASSISTANT_SYSTEM_PROMPT,
        },
        {
            "role": "system",
            "content": (
                f"Current local time: {local_now}\n"
                f"Current UTC time: {utc_now}\n"
                "Use timestamps to interpret relative time phrases.\n\n"
                f"Relevant memories CSV:\n{memory_context}"
            ),
        },
        {
            "role": "user",
            "content": query,
        },
    ]


def format_memory_context_csv(memories: list[MemorySearchResult]) -> str:
    if not memories:
        return ""

    output = StringIO()
    fieldnames = [
        "memory",
        "created_at",
        "updated_at",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for item in memories:
        writer.writerow(
            {
                "memory": item.memory,
                "created_at": item.created_at or "",
                "updated_at": item.updated_at or "",
            }
        )
    return output.getvalue().strip()
