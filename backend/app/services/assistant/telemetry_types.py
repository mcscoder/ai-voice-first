from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, TypeAlias


StageStatus: TypeAlias = Literal[
    "pending",
    "running",
    "done",
    "error",
    "cancelled",
    "skipped",
]


@dataclass
class PipelineStage:
    name: str
    label: str
    status: StageStatus = "pending"
    started_at: float | None = None
    duration_ms: float | None = None
    metadata: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "label": self.label,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "metadata": self.metadata,
        }


@dataclass
class PipelineRun:
    run_id: str
    status: StageStatus
    created_at: str
    started_at: float
    completed_at: float | None
    current_stage: str
    stages: dict[str, PipelineStage]
    metadata: dict[str, object] = field(default_factory=dict)
    total_duration_ms: float | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "status": self.status,
            "created_at": self.created_at,
            "current_stage": self.current_stage,
            "total_duration_ms": self.total_duration_ms,
            "metadata": self.metadata,
            "stages": [stage.to_dict() for stage in self.stages.values()],
        }
