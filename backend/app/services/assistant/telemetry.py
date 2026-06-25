from __future__ import annotations

import json
from collections import deque
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime, timezone
from queue import Empty, Full, Queue
from threading import RLock
from time import perf_counter
from uuid import uuid4

from app.core.config import config


StageStatus = str


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


class AssistantTelemetry:
    """In-memory runtime snapshot for demo and diagnostics dashboards."""

    def __init__(self, max_recent_runs: int = 20) -> None:
        self.max_recent_runs = max_recent_runs
        self._active_runs: dict[str, PipelineRun] = {}
        self._recent_runs: deque[PipelineRun] = deque(maxlen=max_recent_runs)
        self._subscribers: set[Queue[dict[str, object]]] = set()
        self._lock = RLock()

    def start_run(self, language: str | None = None) -> str:
        run_id = uuid4().hex[:12]
        now = perf_counter()
        stages = {
            name: PipelineStage(name=name, label=label)
            for name, label in (
                ("request_received", "Request received"),
                ("asr", "Qwen ASR"),
                ("memory_search", "Vector memory search"),
                ("llm_response_stream", "DeepSeek response stream"),
                ("tts_synthesis", "VieNeu TTS chunks"),
                ("client_stream_done", "Client stream complete"),
                ("mem0_persist_background", "Mem0 background persist"),
            )
        }
        run = PipelineRun(
            run_id=run_id,
            status="running",
            created_at=datetime.now(timezone.utc).isoformat(),
            started_at=now,
            completed_at=None,
            current_stage="request_received",
            stages=stages,
            metadata={"language": language or "auto"},
        )
        run.stages["request_received"].status = "done"
        run.stages["request_received"].duration_ms = 0.0

        with self._lock:
            self._active_runs[run_id] = run
            self._publish_locked()
        return run_id

    def start_stage(self, run_id: str | None, stage_name: str) -> None:
        if run_id is None:
            return
        with self._lock:
            run = self._active_runs.get(run_id)
            if run is None:
                return
            stage = run.stages[stage_name]
            stage.status = "running"
            stage.started_at = perf_counter()
            run.current_stage = stage_name
            self._publish_locked()

    def finish_stage(
        self,
        run_id: str | None,
        stage_name: str,
        metadata: dict[str, object] | None = None,
    ) -> None:
        if run_id is None:
            return
        with self._lock:
            run = self._active_runs.get(run_id)
            if run is None:
                return
            stage = run.stages[stage_name]
            if stage.started_at is not None:
                stage.duration_ms = (perf_counter() - stage.started_at) * 1000
            elif stage.duration_ms is None:
                stage.duration_ms = 0.0
            stage.status = "done"
            if metadata:
                stage.metadata.update(metadata)
            self._publish_locked()

    def finish_stage_with_duration(
        self,
        run_id: str | None,
        stage_name: str,
        duration_ms: float,
        metadata: dict[str, object] | None = None,
    ) -> None:
        if run_id is None:
            return
        with self._lock:
            run = self._active_runs.get(run_id)
            if run is None:
                return
            stage = run.stages[stage_name]
            stage.status = "done"
            stage.duration_ms = duration_ms
            if metadata:
                stage.metadata.update(metadata)
            self._publish_locked()

    def update_stage(
        self,
        run_id: str | None,
        stage_name: str,
        metadata: dict[str, object],
    ) -> None:
        if run_id is None:
            return
        with self._lock:
            run = self._active_runs.get(run_id)
            if run is None:
                return
            run.stages[stage_name].metadata.update(metadata)
            self._publish_locked()

    def fail_run(self, run_id: str | None, message: str) -> None:
        if run_id is None:
            return
        with self._lock:
            run = self._active_runs.get(run_id)
            if run is None:
                return
            run.status = "error"
            run.metadata["error"] = message
            current_stage = run.stages.get(run.current_stage)
            if current_stage and current_stage.status == "running":
                current_stage.status = "error"
                if current_stage.started_at is not None:
                    current_stage.duration_ms = (
                        perf_counter() - current_stage.started_at
                    ) * 1000
            self._complete_locked(run)
            self._publish_locked()

    def complete_run(self, run_id: str | None) -> None:
        if run_id is None:
            return
        with self._lock:
            run = self._active_runs.get(run_id)
            if run is None:
                return
            if run.status != "error":
                run.status = "done"
            self._complete_locked(run)
            self._publish_locked()

    def snapshot(self) -> dict[str, object]:
        with self._lock:
            return self._snapshot_locked()

    def payload(self, snapshot: dict[str, object] | None = None) -> dict[str, object]:
        payload = dict(snapshot or self.snapshot())
        payload["services"] = {
            "asr_model": config.asr.model_name,
            "asr_device": config.asr.device,
            "asr_quantization": config.asr.quantization_level,
            "llm_provider": config.memory.llm_provider,
            "llm_model": config.memory.llm_model,
            "embedder_model": config.memory.embedder_model,
            "tts_device": config.tts.device,
            "tts_voice": config.tts.default_voice,
        }
        return payload

    def sse_event(self, snapshot: dict[str, object]) -> str:
        return f"event: telemetry\ndata: {json.dumps(self.payload(snapshot))}\n\n"

    def reset(self) -> None:
        with self._lock:
            self._active_runs.clear()
            self._recent_runs.clear()
            self._publish_locked()

    def subscribe(
        self,
        keepalive_seconds: float = 15.0,
    ) -> Iterator[dict[str, object] | None]:
        queue: Queue[dict[str, object]] = Queue(maxsize=1)
        with self._lock:
            self._subscribers.add(queue)

        try:
            yield self.snapshot()
            while True:
                try:
                    yield queue.get(timeout=keepalive_seconds)
                except Empty:
                    yield None
        finally:
            with self._lock:
                self._subscribers.discard(queue)

    def _complete_locked(self, run: PipelineRun) -> None:
        now = perf_counter()
        run.completed_at = now
        run.total_duration_ms = (now - run.started_at) * 1000
        self._active_runs.pop(run.run_id, None)
        self._recent_runs.appendleft(run)

    def _publish_locked(self) -> None:
        if not self._subscribers:
            return

        snapshot = self._snapshot_locked()
        for subscriber in list(self._subscribers):
            self._send_latest(subscriber, snapshot)

    def _snapshot_locked(self) -> dict[str, object]:
        active_runs = [run.to_dict() for run in self._active_runs.values()]
        recent_runs = [run.to_dict() for run in self._recent_runs]
        return {
            "active_runs": active_runs,
            "recent_runs": recent_runs,
            "summary": {
                "active_count": len(active_runs),
                "recent_count": len(recent_runs),
            },
        }

    def _send_latest(
        self,
        subscriber: Queue[dict[str, object]],
        snapshot: dict[str, object],
    ) -> None:
        while True:
            try:
                subscriber.put_nowait(snapshot)
                return
            except Full:
                try:
                    subscriber.get_nowait()
                except Empty:
                    return


assistant_telemetry = AssistantTelemetry()
