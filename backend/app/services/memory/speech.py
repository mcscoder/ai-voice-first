from __future__ import annotations

import re


def clean_response_for_speech(text: str) -> str:
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
