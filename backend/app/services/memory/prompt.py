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
    nickname: str = "",
    speaking_style: str = "shortAnswers",
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
            "content": build_personalization_prompt(
                nickname=nickname,
                speaking_style=speaking_style,
            ),
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


def build_personalization_prompt(nickname: str, speaking_style: str) -> str:
    instructions = [
        "Personalization:",
        (
            "Use the user's nickname only when it feels natural or genuinely helpful. "
            "Do not address them by name in every reply."
            if nickname
            else "The user has not set a nickname. Do not invent one."
        ),
    ]
    if nickname:
        instructions.append(f"User nickname: {nickname}")

    style_instruction = {
        "shortAnswers": (
            "Prefer brief replies, usually one to three short sentences unless the user asks for more."
        ),
        "detailedAnswers": (
            "Give fuller context and explanation while keeping the reply voice-friendly."
        ),
        "casual": "Use relaxed, conversational wording.",
        "professional": "Use more formal, direct, polished wording.",
    }.get(
        speaking_style,
        "Prefer brief replies, usually one to three short sentences unless the user asks for more.",
    )
    instructions.append(f"Speaking style: {style_instruction}")
    return "\n".join(instructions)


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
                "You are the memory planner for a Vietnamese voice assistant. "
                "Decide which memory changes should be made from the latest conversation turn. "
                "Use only the provided tool and do not reply with Markdown. "
                "Prefer memories with a clear subject, natural wording, and concise phrasing. "
                "Do not store the assistant's small talk or polite filler."
            ),
        },
        {
            "role": "user",
            "content": (
                "Recent conversation from the last 15 minutes:\n"
                f"{format_recent_messages(recent_messages) or '(none)'}\n\n"
                "Candidate memories from search:\n"
                f"{format_candidate_memories(candidate_memories)}\n\n"
                "Latest user message:\n"
                f"{query}\n\n"
                "Assistant response:\n"
                f"{response_text}\n\n"
                "Rules:\n"
                "- ADD when the latest user message contains new memorable information and it does not duplicate a candidate memory.\n"
                "- UPDATE when the latest user message clarifies, corrects, or adds detail to a candidate memory.\n"
                "- DELETE only when the user clearly says a memory or candidate is no longer true or wants it removed.\n"
                "- NONE when there is no memorable information to store.\n"
                "- For UPDATE or DELETE, id must be one of the ids in Candidate memories.\n"
                "- For ADD or UPDATE, category must be exactly one value from "
                f"{', '.join(MEMORY_CATEGORY_KEYS)}.\n"
                "- Category guide:\n"
                "  about_me = stable facts about the user's identity, background, profile, or enduring personal details.\n"
                "  preferences = the user's own likes, dislikes, habits, favorites, and recurring choices.\n"
                "  work = the user's job, company, projects, responsibilities, work context, or professional tasks.\n"
                "  relationships = people connected to the user and facts about those people or that connection, including names, roles, birthdays, traits, and their preferences.\n"
                "  goals = things the user wants, plans, intends, or is trying to achieve.\n"
                "  custom_notes = memorable facts worth storing that do not clearly fit the other categories.\n"
                "- Choose the most specific category first. preferences, work, relationships, and goals are more specific than about_me.\n"
                "- Use custom_notes only when no other category clearly fits.\n"
                "- If one message contains two distinct memories, create two facts instead of merging them into one.\n"
                "- For people-related memories, split the relationship fact from the detail when both matter. Example: 'The user has a friend named Minh' and 'Minh likes coffee' should be stored as two separate memories.\n"
                "- Use recent conversation only to resolve references such as he, she, they, that person, or that thing.\n"
                "- Call the plan_memory_actions tool with the selected actions."
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
