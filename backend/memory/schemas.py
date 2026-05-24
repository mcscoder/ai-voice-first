from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


MemoryCategory = Literal["finance", "work", "relationship", "plan", "emotion", "general"]
PersonEntityType = Literal["person", "place", "organization"]
FinancialType = Literal["debt_owed", "debt_owed_to", "expense", "income"]


class ExtractedEntity(BaseModel):
    name: str
    type: PersonEntityType = "person"
    role: str = "mentioned"


class ExtractedFinancial(BaseModel):
    amount: float
    currency: str = "VND"
    type: FinancialType = "debt_owed"
    person_name: str | None = None
    due_date: str | None = None


class ExtractedMemory(BaseModel):
    processed_text: str
    category: MemoryCategory = "general"
    subcategory: str | None = None
    entities: list[ExtractedEntity] = Field(default_factory=list)
    financial: ExtractedFinancial | None = None
    sentiment: float = 0.0
    importance: int = 1
    emotional_tags: list[str] = Field(default_factory=list)
    time_references: list[str] = Field(default_factory=list)


class StoredMemory(BaseModel):
    id: str
    user_id: str
    raw_text: str
    processed_text: str
    category: MemoryCategory
    subcategory: str | None = None
    sentiment: float
    importance: int
    metadata: dict[str, object] = Field(default_factory=dict)
    created_at: str


class PersonSummary(BaseModel):
    id: str
    name: str
    aliases: list[str] = Field(default_factory=list)
    relationship_type: str = "friend"
    trust_score: float = 0.5
    interaction_count: int = 0
    last_interaction_at: str | None = None
