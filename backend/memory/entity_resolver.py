from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher

from .schemas import ExtractedEntity, PersonSummary


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_name(name: str) -> str:
    return " ".join(name.strip().lower().split())


@dataclass(slots=True)
class ResolvedEntity:
    person: PersonSummary
    created: bool


class EntityResolver:
    def resolve_entities(
        self,
        connection: sqlite3.Connection,
        user_id: str,
        entities: list[ExtractedEntity],
    ) -> list[ResolvedEntity]:
        resolved: list[ResolvedEntity] = []
        for entity in entities:
            if entity.type != "person":
                continue
            person = self._resolve_person(connection, user_id, entity.name)
            resolved.append(person)
        return resolved

    def _resolve_person(
        self,
        connection: sqlite3.Connection,
        user_id: str,
        raw_name: str,
    ) -> ResolvedEntity:
        candidates = self._load_people(connection, user_id)
        normalized = _normalize_name(raw_name)

        for candidate in candidates:
            aliases = [candidate.name, *candidate.aliases]
            if normalized in {_normalize_name(alias) for alias in aliases}:
                return self._update_person(connection, candidate.id, candidate, raw_name)

            if any(
                SequenceMatcher(None, normalized, _normalize_name(alias)).ratio() >= 0.84
                for alias in aliases
            ):
                return self._update_person(connection, candidate.id, candidate, raw_name)

        return self._create_person(connection, user_id, raw_name)

    def _load_people(self, connection: sqlite3.Connection, user_id: str) -> list[PersonSummary]:
        rows = connection.execute(
            """
            SELECT id, name, aliases_json, relationship_type, trust_score,
                   interaction_count, last_interaction_at
            FROM people
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchall()
        people: list[PersonSummary] = []
        for row in rows:
            people.append(
                PersonSummary(
                    id=str(row["id"]),
                    name=str(row["name"]),
                    aliases=json.loads(row["aliases_json"]),
                    relationship_type=str(row["relationship_type"]),
                    trust_score=float(row["trust_score"]),
                    interaction_count=int(row["interaction_count"]),
                    last_interaction_at=row["last_interaction_at"],
                )
            )
        return people

    def _create_person(self, connection: sqlite3.Connection, user_id: str, raw_name: str) -> ResolvedEntity:
        person_id = str(uuid.uuid4())
        now = _utcnow()
        person = PersonSummary(
            id=person_id,
            name=raw_name.strip(),
            aliases=[],
            relationship_type="friend",
            trust_score=0.5,
            interaction_count=1,
            last_interaction_at=now,
        )
        connection.execute(
            """
            INSERT INTO people (
                id, user_id, name, aliases_json, relationship_type, trust_score,
                interaction_count, last_interaction_at, metadata_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                person_id,
                user_id,
                person.name,
                json.dumps(person.aliases, ensure_ascii=False),
                person.relationship_type,
                person.trust_score,
                person.interaction_count,
                person.last_interaction_at,
                json.dumps({}, ensure_ascii=False),
                now,
                now,
            ),
        )
        return ResolvedEntity(person=person, created=True)

    def _update_person(
        self,
        connection: sqlite3.Connection,
        person_id: str,
        existing: PersonSummary,
        raw_name: str,
    ) -> ResolvedEntity:
        aliases = list(dict.fromkeys([*existing.aliases, raw_name.strip()]))
        now = _utcnow()
        trust_score = min(1.0, existing.trust_score + 0.02)
        interaction_count = existing.interaction_count + 1
        person = PersonSummary(
            id=person_id,
            name=existing.name,
            aliases=aliases,
            relationship_type=existing.relationship_type,
            trust_score=trust_score,
            interaction_count=interaction_count,
            last_interaction_at=now,
        )
        connection.execute(
            """
            UPDATE people
            SET aliases_json = ?, trust_score = ?, interaction_count = ?,
                last_interaction_at = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                json.dumps(aliases, ensure_ascii=False),
                trust_score,
                interaction_count,
                now,
                now,
                person_id,
            ),
        )
        return ResolvedEntity(person=person, created=False)
