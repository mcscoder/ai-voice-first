from __future__ import annotations

from app.services.assistant.telemetry import AssistantTelemetry
from app.services.assistant.types import AssistantMemory, ResponseHolder


class StreamPersistence:
    def __init__(
        self,
        memory: AssistantMemory,
        telemetry: AssistantTelemetry,
        user_id: str,
    ) -> None:
        self.memory = memory
        self.telemetry = telemetry
        self.user_id = user_id

    def persist_streamed_response(self, response_holder: ResponseHolder) -> None:
        query = response_holder.get("query", "").strip()
        response_text = response_holder.get("text", "").strip()
        run_id = response_holder.get("run_id")

        self.telemetry.start_stage(run_id, "mem0_persist_background")
        if response_holder.get("completed") != "true" or not query or not response_text:
            self.telemetry.finish_stage(
                run_id,
                "mem0_persist_background",
                {
                    "persisted": False,
                    "skip_reason": self._persist_skip_reason(response_holder),
                },
                status="skipped",
            )
            self.telemetry.complete_run(run_id)
            return

        persist_result = self.memory.persist_conversation(
            query,
            response_text,
            self.user_id,
        )
        persist_metadata: dict[str, object] = {
            "persisted": True,
        }
        if persist_result is not None:
            persist_metadata.update(
                {
                    "memory_actions": persist_result.actions,
                    "action_counts": persist_result.action_counts,
                }
            )
        self.telemetry.finish_stage(
            run_id,
            "mem0_persist_background",
            persist_metadata,
        )
        self.telemetry.complete_run(run_id)

    def _persist_skip_reason(self, response_holder: ResponseHolder) -> str:
        if response_holder.get("cancelled") == "true":
            return response_holder.get("cancel_reason", "client_disconnected")
        if not response_holder.get("query", "").strip():
            return "missing_query"
        if not response_holder.get("text", "").strip():
            return "missing_response"
        return "stream_not_completed"
