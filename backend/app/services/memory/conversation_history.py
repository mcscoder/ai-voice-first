from __future__ import annotations

from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import RLock
from typing import Literal


ConversationRole = Literal["user", "assistant"]


@dataclass(frozen=True)
class ConversationMessage:
    role: ConversationRole
    content: str
    created_at: datetime


class ConversationHistory:
    """In-memory short-term conversation history keyed by user id."""

    def __init__(
        self,
        window: timedelta = timedelta(minutes=15),
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self.window = window
        self._now = now or (lambda: datetime.now(timezone.utc))
        self._messages: dict[str, deque[ConversationMessage]] = {}
        self._lock = RLock()

    def messages_for(self, user_id: str) -> list[dict[str, str]]:
        with self._lock:
            now = self._now()
            self._prune_locked(user_id, now)
            messages = self._messages.get(user_id, deque())
            return [
                {"role": message.role, "content": message.content}
                for message in messages
            ]

    def record_turn(self, user_id: str, query: str, response_text: str) -> None:
        now = self._now()
        with self._lock:
            self._prune_locked(user_id, now)
            messages = self._messages.setdefault(user_id, deque())
            messages.append(
                ConversationMessage("user", query.strip(), now),
            )
            messages.append(
                ConversationMessage("assistant", response_text.strip(), now),
            )

    def clear(self) -> None:
        with self._lock:
            self._messages.clear()

    def _prune_locked(self, user_id: str, now: datetime) -> None:
        cutoff = now - self.window
        messages = self._messages.get(user_id)
        if messages is None:
            return
        while messages and messages[0].created_at < cutoff:
            messages.popleft()
        if not messages:
            self._messages.pop(user_id, None)


conversation_history = ConversationHistory()
