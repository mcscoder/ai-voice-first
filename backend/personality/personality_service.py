from __future__ import annotations


class PersonalityService:
    def __init__(self, default_personality: str = "serious") -> None:
        self.default_personality = default_personality

    def resolve_personality(self, requested_personality: str | None) -> str:
        if requested_personality in {"chill", "mildly_toxic", "serious", "chaotic_bestie"}:
            return requested_personality
        return self.default_personality
