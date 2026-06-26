from __future__ import annotations


def memory_actions(raw_result: object) -> list[dict[str, object]]:
    actions: list[dict[str, object]] = []
    returned_results = raw_result.get("results", []) if isinstance(raw_result, dict) else []

    # Only use structured return values from mem0; log-derived actions are intentionally ignored.
    if isinstance(returned_results, list):
        for item in returned_results:
            if isinstance(item, dict) and isinstance(item.get("event"), str):
                actions.append(normalize_memory_action(item))

    return actions


def normalize_memory_action(action: dict[str, object]) -> dict[str, object]:
    memory_text = action.get("memory") or action.get("text") or ""
    previous_memory = action.get("previous_memory") or action.get("old_memory")
    normalized: dict[str, object] = {
        "id": str(action.get("id", "")),
        "event": str(action["event"]),
        "memory": str(memory_text),
    }
    if previous_memory:
        normalized["previous_memory"] = str(previous_memory)
    return normalized


def memory_action_counts(actions: list[dict[str, object]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for action in actions:
        event = str(action.get("event", "UNKNOWN"))
        counts[event] = counts.get(event, 0) + 1
    return counts
