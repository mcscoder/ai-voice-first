from __future__ import annotations

import csv
from datetime import datetime, timezone
from io import StringIO

from app.services.memory.categories import MEMORY_CATEGORY_KEYS
from app.services.memory.types import MemorySearchResult


VOICE_ASSISTANT_SYSTEM_PROMPT = """You generate final text for VieNeu-TTS.
Return only plain speakable text for tts.infer(text=...).
Use plain spoken text only.
Write mainly in natural Vietnamese unless the user asks otherwise. Sound like a real human assistant. Keep replies warm, conversational, concise, and easy to say aloud. Use complete sentences, short sentence length, and punctuation for natural pauses.
Do not use Markdown, bullets, tables, headings, code blocks, links, citations, emojis, labels, stage directions, or explanations about TTS.
Make all text voice-friendly. Convert numbers, dates, times, currencies, symbols, measurements, and abbreviations into spoken form. Spell English abbreviations when needed, for example API as A P I. Keep English technical terms only when they sound more natural than translating them.
If the user asks for lists, code, links, tables, or dense technical details, summarize them in smooth spoken prose and mention that details can be shown on screen.
Final output must contain only the text to be spoken.
"""


def build_response_messages(
    query: str,
    memories: list[MemorySearchResult],
    recent_messages: list[dict[str, str]] | None = None,
) -> list[dict[str, str]]:
    local_now = datetime.now().astimezone().isoformat()
    utc_now = datetime.now(timezone.utc).isoformat()
    memory_context = format_memory_context_csv(memories)
    if not memory_context:
        memory_context = "No relevant memories yet."

    messages = [
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
    ]
    messages.extend(recent_messages or [])
    messages.append(
        {
            "role": "user",
            "content": query,
        },
    )
    return messages


def build_memory_planner_messages(
    query: str,
    response_text: str,
    recent_messages: list[dict[str, str]],
    candidate_memories: list[MemorySearchResult],
) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "Bạn là bộ lập kế hoạch ghi nhớ cho trợ lý giọng nói tiếng Việt. "
                "Hãy quyết định các thay đổi memory cần thực hiện từ lượt hội thoại mới nhất. "
                "Chỉ dùng tool được cung cấp, không trả lời bằng Markdown. "
                "Ưu tiên memory rõ chủ thể, tự nhiên, "
                "ngắn gọn, và không lưu câu trả lời xã giao của assistant."
            ),
        },
        {
            "role": "user",
            "content": (
                "Recent conversation trong 15 phút gần đây:\n"
                f"{format_recent_messages(recent_messages) or '(none)'}\n\n"
                "Candidate memories đã search được:\n"
                f"{format_candidate_memories(candidate_memories)}\n\n"
                "Latest user message:\n"
                f"{query}\n\n"
                "Assistant response:\n"
                f"{response_text}\n\n"
                "Quy tắc:\n"
                "- ADD khi latest user message chứa thông tin mới đáng nhớ và không trùng candidate.\n"
                "- UPDATE khi latest user message làm rõ, sửa, hoặc bổ sung một candidate memory.\n"
                "- DELETE chỉ khi user nói rõ memory/candidate đó không còn đúng hoặc muốn xóa.\n"
                "- NONE khi không có thông tin đáng nhớ.\n"
                "- Với UPDATE/DELETE, id phải là một id trong Candidate memories.\n"
                "- Với ADD/UPDATE, category phải là đúng một giá trị trong "
                f"{', '.join(MEMORY_CATEGORY_KEYS)}.\n"
                "- Dùng recent conversation chỉ để giải tham chiếu như nó, thằng đó, người đó, bạn kia.\n"
                "- Gọi tool plan_memory_actions với actions đã chọn."
            ),
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


def format_recent_messages(messages: list[dict[str, str]]) -> str:
    lines: list[str] = []
    for message in messages:
        role = message.get("role", "").strip()
        content = message.get("content", "").strip()
        if not role or not content:
            continue
        lines.append(f"{role}: {content}")
    return "\n".join(lines)


def format_candidate_memories(candidate_memories: list[MemorySearchResult]) -> str:
    lines: list[str] = []
    for item in candidate_memories:
        if not item.id:
            continue
        score = "" if item.score is None else f" score={item.score}"
        lines.append(f"id={item.id}{score} memory={item.memory}")
    return "\n".join(lines) or "(none)"
