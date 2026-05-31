from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol


FINANCE_QUERY_TERMS = {
    "nợ",
    "tiền",
    "trả",
    "debt",
    "money",
    "owe",
    "owed",
}
CATEGORY_HINTS = {
    "finance": FINANCE_QUERY_TERMS,
    "plan": {"mai", "tuần", "lịch", "hẹn", "plan", "schedule", "meet"},
}


class EmbeddingProvider(Protocol):
    is_enabled: bool
    model_name: str

    def embed(self, text: str) -> list[float] | None:
        ...


@dataclass(slots=True)
class MemorySearchResult:
    memory_id: str
    processed_text: str
    category: str
    importance: int
    created_at: str
    score: float
    person_name: str | None = None
    amount: float | None = None
    currency: str | None = None
    status: str | None = None
    financial_type: str | None = None


def row_to_result(row: sqlite3.Row, *, score: float) -> MemorySearchResult:
    return MemorySearchResult(
        memory_id=str(row["id"]),
        processed_text=str(row["processed_text"]),
        category=str(row["category"]),
        importance=int(row["importance"]),
        created_at=str(row["created_at"]),
        person_name=str(row["person_name"]) if row["person_name"] else None,
        amount=float(row["amount"]) if row["amount"] is not None else None,
        currency=str(row["currency"]) if row["currency"] else None,
        status=str(row["status"]) if row["status"] else None,
        financial_type=str(row["financial_type"]) if "financial_type" in row.keys() and row["financial_type"] else None,
        score=score,
    )


def timestamp_score(value: str) -> float:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return 0.0
    return parsed.astimezone(timezone.utc).timestamp()
