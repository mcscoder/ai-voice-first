from __future__ import annotations

import re

from .text_similarity import tokenize


RECALL_TERMS = {
    "nợ",
    "tiền",
    "gặp",
    "lần cuối",
    "nhớ",
    "debt",
    "owe",
    "owed",
    "remember",
    "last",
}
QUESTION_TERMS = {
    "ai",
    "bao nhiêu",
    "khi nào",
    "lúc nào",
    "ở đâu",
    "cái gì",
    "gì",
    "who",
    "how much",
    "when",
    "where",
    "what",
}
QUESTION_MARKERS = (
    "bao nhiêu",
    "khi nào",
    "lúc nào",
    "ở đâu",
    "cái gì",
    "who",
    "how much",
    "when",
    "where",
)


def should_store_memory_transcript(transcript: str) -> bool:
    normalized = normalize_query_text(transcript)
    if not normalized:
        return False
    if not looks_like_question(normalized):
        return True

    tokens = tokenize(normalized)
    has_recall_term = _contains_any(normalized, tokens, RECALL_TERMS)
    has_question_term = _contains_any(normalized, tokens, QUESTION_TERMS)
    return not (has_recall_term or has_question_term)


def normalize_query_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def looks_like_question(text: str) -> bool:
    if text.endswith("?"):
        return True
    tokens = tokenize(text)
    if tokens & {"ai", "who", "when", "where", "what"}:
        return True
    return any(_contains_phrase(text, marker) for marker in QUESTION_MARKERS)


def _contains_any(text: str, tokens: set[str], terms: set[str]) -> bool:
    for term in terms:
        if " " in term:
            if _contains_phrase(text, term):
                return True
        elif term in tokens:
            return True
    return False


def _contains_phrase(text: str, phrase: str) -> bool:
    pattern = rf"(?<!\w){re.escape(phrase)}(?!\w)"
    return bool(re.search(pattern, text))
