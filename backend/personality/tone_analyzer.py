from __future__ import annotations


class ToneAnalyzer:
    def analyze(self, transcript: str) -> dict[str, object]:
        lowered = transcript.lower()
        emoji_count = sum(1 for char in transcript if char in "😀😁😂🤣🙂🙃😉😎😈💀🔥")
        swearing = sum(lowered.count(word) for word in ("đm", "dm", "vãi", "cặc", "đụ", "lồn"))
        formality = 1.0
        if "ạ" in lowered or "xin chào" in lowered:
            formality += 0.5
        if swearing:
            formality -= 0.3
        return {
            "emoji_count": emoji_count,
            "swearing_count": swearing,
            "formality": max(0.0, min(1.0, formality)),
        }
