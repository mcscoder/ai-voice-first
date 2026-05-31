from __future__ import annotations

import re
from difflib import SequenceMatcher


IMPORTANT_SHORT_TOKENS = {"ai", "nợ"}


def tokenize(text: str) -> set[str]:
    return {
        token.lower()
        for token in re.findall(r"[\wÀ-ỹ']+", text)
        if len(token) > 2 or token.lower() in IMPORTANT_SHORT_TOKENS
    }


def memory_similarity(
    source_text: str,
    candidate_text: str,
    *,
    source_tokens: set[str],
) -> float:
    candidate_tokens = tokenize(candidate_text)
    union = source_tokens | candidate_tokens
    overlap = 0.0 if not union else len(source_tokens & candidate_tokens) / len(union)
    text_ratio = SequenceMatcher(
        None,
        source_text.lower(),
        candidate_text.lower(),
    ).ratio()
    return max(overlap, text_ratio)


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or not left:
        return 0.0

    dot = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = sum(value * value for value in left) ** 0.5
    right_norm = sum(value * value for value in right) ** 0.5
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return dot / (left_norm * right_norm)
