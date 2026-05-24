from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path


DEFAULT_DB_FILENAME = "knowledge-brain.sqlite3"


class DatabaseEngine:
    def __init__(self, database_path: str | None = None) -> None:
        raw_path = database_path or os.getenv("KNOWLEDGE_BRAIN_DB_PATH")
        if raw_path:
            self.database_path = Path(raw_path).expanduser()
        else:
            self.database_path = Path(__file__).resolve().parents[1] / ".data" / DEFAULT_DB_FILENAME

        self.database_path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def connection(self):
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()


_engine: DatabaseEngine | None = None


def get_database_engine() -> DatabaseEngine:
    global _engine
    if _engine is None:
        _engine = DatabaseEngine()
    return _engine
