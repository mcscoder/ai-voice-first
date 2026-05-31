from __future__ import annotations

from .retrieval_records import MemorySearchResult


class MemoryContextBuilder:
    def __init__(self, *, character_budget: int = 1600) -> None:
        self._character_budget = character_budget

    def build(self, results: list[MemorySearchResult]) -> str:
        if not results:
            return ""

        lines = ["[MEMORY CONTEXT]"]
        used_memory_ids: set[str] = set()
        for result in results:
            if result.memory_id in used_memory_ids:
                continue
            used_memory_ids.add(result.memory_id)
            line = self._format_result(result)
            if self._would_exceed_budget(lines, line):
                break
            lines.append(line)
        if len(lines) == 1:
            return ""
        lines.append("[/MEMORY CONTEXT]")
        return "\n".join(lines)

    def _format_result(self, result: MemorySearchResult) -> str:
        line = f"- {result.processed_text} ({result.category}, {result.created_at})"
        details: list[str] = []
        if result.person_name:
            details.append(f"person={result.person_name}")
        if result.amount is not None:
            amount = f"{result.amount:g}"
            details.append(f"amount={amount} {result.currency or ''}".strip())
        if result.status:
            details.append(f"status={result.status}")
        if details:
            line = f"{line} [{', '.join(details)}]"
        return line

    def _would_exceed_budget(self, lines: list[str], next_line: str) -> bool:
        return len("\n".join([*lines, next_line, "[/MEMORY CONTEXT]"])) > self._character_budget
