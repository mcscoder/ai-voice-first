from __future__ import annotations


EXTRACTION_PROMPT = """
You extract structured memories from Vietnamese and English speech.
Return one JSON object only. No markdown. No prose.

Schema:
{
  "processed_text": "normalized transcript text",
  "category": "finance | work | relationship | plan | emotion | general",
  "subcategory": "optional short label or null",
  "entities": [{"name":"string","type":"person | place | organization","role":"mentioned"}],
  "financial": {
    "amount": 0,
    "currency": "VND",
    "type": "debt_owed | debt_owed_to | expense | income",
    "person_name": "optional string or null",
    "due_date": "optional string or null"
  } or null,
  "sentiment": -1.0,
  "importance": 1,
  "emotional_tags": ["optional short tags"],
  "time_references": ["optional short phrases"]
}

Rules:
- Preserve the meaning of the transcript in processed_text.
- Use the transcript language for processed_text.
- Only include entities that are explicitly mentioned or strongly implied.
- sentiment must be a float from -1.0 to 1.0.
- importance must be an integer from 1 to 10.
- If no financial memory is present, set financial to null.
"""

PERSONALITY_PROMPTS: dict[str, str] = {
    "chill": "Relaxed, concise, friendly.",
    "mildly_toxic": "Playful, sarcastic, never cruel.",
    "serious": "Professional, direct, concise.",
    "chaotic_bestie": "Chaotic but supportive, informal Vietnamese slang okay.",
}
