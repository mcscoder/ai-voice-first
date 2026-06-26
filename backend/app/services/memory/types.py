from __future__ import annotations

from dataclasses import dataclass, field

from app.services.memory.persistence import MemoryAction


@dataclass(frozen=True)
class MemoryReply:
    text: str
    user_id: str


@dataclass(frozen=True)
class MemorySearchResult:
    memory: str
    score: float | None
    id: str | None = None
    user_id: str | None = None
    categories: list[str] = field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None
    agent_id: str | None = None
    run_id: str | None = None
    actor_id: str | None = None
    role: str | None = None
    metadata: dict[str, object] | None = None
    extra_fields: dict[str, object] = field(default_factory=dict)

    @classmethod
    def from_mem0(cls, item: dict[str, object]) -> MemorySearchResult:
        memory_text = item.get("memory")
        if not isinstance(memory_text, str):
            raise ValueError("Mem0 search result is missing memory text.")

        known_keys = {
            "id",
            "memory",
            "score",
            "user_id",
            "categories",
            "created_at",
            "updated_at",
            "agent_id",
            "run_id",
            "actor_id",
            "role",
            "metadata",
        }
        score = item.get("score")
        raw_categories = item.get("categories")
        categories = raw_categories if isinstance(raw_categories, list) else []
        metadata = item.get("metadata")

        return cls(
            id=str(item["id"]) if item.get("id") is not None else None,
            memory=memory_text,
            score=float(score) if isinstance(score, (int, float)) else None,
            user_id=str(item["user_id"]) if item.get("user_id") is not None else None,
            categories=[str(category) for category in categories],
            created_at=str(item["created_at"])
            if item.get("created_at") is not None
            else None,
            updated_at=str(item["updated_at"])
            if item.get("updated_at") is not None
            else None,
            agent_id=str(item["agent_id"]) if item.get("agent_id") is not None else None,
            run_id=str(item["run_id"]) if item.get("run_id") is not None else None,
            actor_id=str(item["actor_id"]) if item.get("actor_id") is not None else None,
            role=str(item["role"]) if item.get("role") is not None else None,
            metadata=metadata if isinstance(metadata, dict) else None,
            extra_fields={key: value for key, value in item.items() if key not in known_keys},
        )

    def as_telemetry(self) -> dict[str, object]:
        telemetry = dict(self.extra_fields)
        for key in (
            "id",
            "user_id",
            "categories",
            "created_at",
            "updated_at",
            "agent_id",
            "run_id",
            "actor_id",
            "role",
            "metadata",
        ):
            value = getattr(self, key)
            if value:
                telemetry[key] = value
        telemetry["memory"] = self.memory
        telemetry["score"] = self.score
        return telemetry


@dataclass(frozen=True)
class MemoryPersistResult:
    actions: list[MemoryAction]
    action_counts: dict[str, int]
    raw_result: dict[str, object] | None


class MemoryServiceError(Exception):
    pass
