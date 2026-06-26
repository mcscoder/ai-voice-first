from __future__ import annotations

from app.services.assistant.telemetry import AssistantTelemetry
from app.services.assistant.types import AssistantMemory, ResponseHolder
from app.services.memory.conversation_history import ConversationHistory
from app.services.memory import MemorySearchResult


class StreamPersistence:
    def __init__(
        self,
        memory: AssistantMemory,
        telemetry: AssistantTelemetry,
        history: ConversationHistory,
    ) -> None:
        self.memory = memory
        self.telemetry = telemetry
        self.history = history

    def persist_streamed_response(self, response_holder: ResponseHolder) -> None:
        query = str(response_holder.get("query", "")).strip()
        response_text = str(response_holder.get("text", "")).strip()
        user_id = str(response_holder.get("user_id", "")).strip()
        run_id = response_holder.get("run_id")

        self.telemetry.start_stage(run_id, "mem0_persist_background")
        if (
            response_holder.get("completed") != "true"
            or not query
            or not response_text
            or not user_id
        ):
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

        if response_holder.get("memory_enabled") is False:
            self.telemetry.finish_stage(
                run_id,
                "mem0_persist_background",
                {
                    "persisted": False,
                    "skip_reason": "memory_disabled",
                },
                status="skipped",
            )
            self.history.record_turn(user_id, query, response_text)
            self.telemetry.complete_run(run_id)
            return

        candidate_memories = self._candidate_memories(response_holder)
        persist_result = self.memory.persist_conversation(
            query,
            response_text,
            user_id,
            self._recent_messages(response_holder),
            candidate_memories,
        )
        self.history.record_turn(user_id, query, response_text)
        persist_metadata: dict[str, object] = {
            "persisted": True,
            "candidate_memory_count": len(candidate_memories),
        }
        if persist_result is not None:
            persist_metadata.update(
                {
                    "memory_actions": [
                        action.to_dict() for action in persist_result.actions
                    ],
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
            return str(response_holder.get("cancel_reason", "client_disconnected"))
        if not str(response_holder.get("query", "")).strip():
            return "missing_query"
        if not str(response_holder.get("text", "")).strip():
            return "missing_response"
        if not str(response_holder.get("user_id", "")).strip():
            return "missing_user"
        return "stream_not_completed"

    def _recent_messages(
        self,
        response_holder: ResponseHolder,
    ) -> list[dict[str, str]]:
        recent_messages = response_holder.get("recent_messages")
        if not isinstance(recent_messages, list):
            return []

        messages: list[dict[str, str]] = []
        for message in recent_messages:
            if not isinstance(message, dict):
                continue
            role = message.get("role")
            content = message.get("content")
            if isinstance(role, str) and isinstance(content, str):
                messages.append({"role": role, "content": content})
        return messages

    def _candidate_memories(
        self,
        response_holder: ResponseHolder,
    ) -> list[MemorySearchResult]:
        candidate_memories = response_holder.get("candidate_memories")
        if not isinstance(candidate_memories, list):
            return []
        return [
            item for item in candidate_memories if isinstance(item, MemorySearchResult)
        ]
