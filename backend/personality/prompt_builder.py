from __future__ import annotations

from .presets import PERSONALITIES


class PersonalityPromptBuilder:
    def build_system_prompt(
        self,
        personality: str,
        language: str,
        memory_context: str | None = None,
        user_tone_profile: dict | None = None,
    ) -> str:
        fragments = [
            f"You are responding in {language}.",
            PERSONALITIES.get(personality, PERSONALITIES["serious"])["system_prompt_fragment"],
        ]
        if memory_context:
            fragments.append(f"Relevant memory context:\n{memory_context}")
        if user_tone_profile:
            fragments.append(f"Tone profile: {user_tone_profile}")
        return "\n\n".join(fragments)
