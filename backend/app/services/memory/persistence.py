from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


MemoryActionEvent = Literal["ADD", "UPDATE", "DELETE", "NONE"]

MEMORY_PLANNER_TOOL = {
    "type": "function",
    "function": {
        "name": "plan_memory_actions",
        "description": "Plan exact memory mutations for the latest conversation turn.",
        "strict": True,
        "parameters": {
            "type": "object",
            "additionalProperties": False,
            "required": ["actions"],
            "properties": {
                "actions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["event", "id", "memory"],
                        "properties": {
                            "event": {
                                "type": "string",
                                "enum": ["ADD", "UPDATE", "DELETE", "NONE"],
                            },
                            "id": {
                                "type": "string",
                                "description": (
                                    "Candidate memory id for UPDATE or DELETE; empty "
                                    "string for ADD or NONE."
                                ),
                            },
                            "memory": {
                                "type": "string",
                                "description": (
                                    "New memory text for ADD or UPDATE; empty string "
                                    "for DELETE or NONE."
                                ),
                            },
                        },
                    },
                }
            },
        },
    },
}


@dataclass(frozen=True)
class MemoryAction:
    event: MemoryActionEvent
    memory: str = ""
    id: str = ""
    previous_memory: str = ""

    def to_dict(self) -> dict[str, object]:
        action: dict[str, object] = {
            "event": self.event,
            "memory": self.memory,
        }
        if self.id or self.event == "ADD":
            action["id"] = self.id
        if self.previous_memory:
            action["previous_memory"] = self.previous_memory
        return action


def memory_action_counts(actions: list[MemoryAction]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for action in actions:
        counts[action.event] = counts.get(action.event, 0) + 1
    return counts
