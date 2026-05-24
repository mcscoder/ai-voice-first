from __future__ import annotations

from dataclasses import dataclass


SCHEMA_STATEMENTS: tuple[str, ...] = (
    """
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS memories (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        raw_text TEXT NOT NULL,
        processed_text TEXT NOT NULL,
        category TEXT NOT NULL,
        subcategory TEXT,
        sentiment REAL NOT NULL,
        importance INTEGER NOT NULL,
        metadata_json TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS people (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        name TEXT NOT NULL,
        aliases_json TEXT NOT NULL,
        relationship_type TEXT NOT NULL,
        trust_score REAL NOT NULL,
        interaction_count INTEGER NOT NULL,
        last_interaction_at TEXT,
        metadata_json TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS financial_records (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        memory_id TEXT NOT NULL,
        person_id TEXT,
        type TEXT NOT NULL,
        amount REAL NOT NULL,
        currency TEXT NOT NULL,
        status TEXT NOT NULL,
        due_date TEXT,
        settled_at TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (memory_id) REFERENCES memories(id),
        FOREIGN KEY (person_id) REFERENCES people(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS memory_links (
        id TEXT PRIMARY KEY,
        source_memory_id TEXT NOT NULL,
        target_memory_id TEXT NOT NULL,
        link_type TEXT NOT NULL,
        strength REAL NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (source_memory_id) REFERENCES memories(id),
        FOREIGN KEY (target_memory_id) REFERENCES memories(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS memory_embeddings (
        id TEXT PRIMARY KEY,
        memory_id TEXT NOT NULL UNIQUE,
        embedding_json TEXT NOT NULL,
        model_name TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (memory_id) REFERENCES memories(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS personality_settings (
        user_id TEXT PRIMARY KEY,
        personality_key TEXT NOT NULL,
        tone_profile_json TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS reminders (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        memory_id TEXT,
        person_id TEXT,
        type TEXT NOT NULL,
        trigger_condition_json TEXT NOT NULL,
        message TEXT NOT NULL,
        scheduled_at TEXT,
        delivered INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (memory_id) REFERENCES memories(id),
        FOREIGN KEY (person_id) REFERENCES people(id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_memories_user_created_at
    ON memories(user_id, created_at DESC)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_memories_user_category
    ON memories(user_id, category)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_people_user_name
    ON people(user_id, name)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_financial_records_user_person_status
    ON financial_records(user_id, person_id, status)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_memory_links_source
    ON memory_links(source_memory_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_memory_links_target
    ON memory_links(target_memory_id)
    """,
)


@dataclass(slots=True)
class MemorySchemaVersion:
    version: int = 1


def bootstrap_schema(connection) -> None:
    for statement in SCHEMA_STATEMENTS:
        connection.execute(statement)
