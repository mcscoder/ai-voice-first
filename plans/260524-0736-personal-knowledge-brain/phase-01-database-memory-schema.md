---
phase: 1
title: "Database & Memory Schema"
status: pending
priority: P1
effort: "12h"
dependencies: []
---

# Phase 1: Database & Memory Schema

## Overview

Design and implement the PostgreSQL database schema that powers the entire memory system. This is the foundation — every other phase depends on this schema being right.

## Requirements

### Functional
- Store individual memories with category, content, entities, timestamps
- Store person profiles with relationship metadata
- Store financial records (debts, payments)
- Support vector embeddings for semantic search
- Track memory relationships (links between memories)
- Support user-scoped data isolation

### Non-functional
- Query performance: < 100ms for single memory retrieval
- Vector search: < 500ms for top-10 similar memories
- Schema must support future categories without migration

## Architecture

### Database: PostgreSQL + pgvector

```sql
-- Core tables
users
memories
memory_categories
people (entities the user talks about)
financial_records
memory_links (graph edges)
memory_embeddings (pgvector)
personality_settings
reminders
```

### Data Flow

```
Voice Input → Transcription → Memory Extraction
                                    ↓
                            memories table
                                    ↓
                    memory_embeddings (vector)
                    memory_links (graph edges)
                    people (entity extraction)
                    financial_records (if money)
```

## Related Code Files

### Create
- `backend/database/__init__.py` — DB package init
- `backend/database/engine.py` — SQLAlchemy async engine + session factory
- `backend/database/models.py` — All SQLAlchemy ORM models
- `backend/database/migrations/` — Alembic migration directory
- `backend/alembic.ini` — Alembic configuration

### Modify
- `backend/main.py` — Add DB lifespan (connect/disconnect)
- `backend/.env.example` — Add DATABASE_URL
- `backend/pyproject.toml` — Add sqlalchemy, asyncpg, alembic, pgvector deps

## Implementation Steps

1. **Add dependencies** to `pyproject.toml`:
   ```
   sqlalchemy[asyncio] >= 2.0
   asyncpg
   alembic
   pgvector
   ```

2. **Create database engine** (`backend/database/engine.py`):
   - Async engine from `DATABASE_URL` env var
   - Async session factory with scoped sessions
   - Connection pool configuration (pool_size=5, max_overflow=10)

3. **Design and implement models** (`backend/database/models.py`):
   ```python
   class User(Base):
       id: UUID (PK)
       created_at, updated_at

   class Memory(Base):
       id: UUID (PK)
       user_id: FK → users
       raw_text: str  # Original transcribed text
       processed_text: str  # LLM-cleaned version
       category: Enum (finance, work, relationship, plan, emotion, general)
       subcategory: str (nullable)
       sentiment: float (-1.0 to 1.0)
       importance: int (1-10)
       metadata: JSONB  # Flexible extra data
       created_at, updated_at

   class Person(Base):
       id: UUID (PK)
       user_id: FK → users
       name: str
       aliases: ARRAY[str]  # "Minh", "thằng Minh", "anh Minh"
       relationship_type: str  # friend, colleague, family
       trust_score: float (0-1)
       interaction_count: int
       last_interaction_at: timestamp
       metadata: JSONB
       created_at, updated_at

   class FinancialRecord(Base):
       id: UUID (PK)
       user_id: FK → users
       memory_id: FK → memories
       person_id: FK → people (nullable)
       type: Enum (debt_owed, debt_owed_to, expense, income)
       amount: Decimal
       currency: str (default 'VND')
       status: Enum (pending, partial, settled)
       due_date: date (nullable)
       settled_at: timestamp (nullable)
       created_at

   class MemoryLink(Base):
       id: UUID (PK)
       source_memory_id: FK → memories
       target_memory_id: FK → memories
       link_type: str  # related, contradicts, follows, updates
       strength: float (0-1)
       created_at

   class MemoryEmbedding(Base):
       id: UUID (PK)
       memory_id: FK → memories (unique)
       embedding: Vector(384)  # MiniLM dimension
       model_name: str

   class PersonMemory(Base):  # Junction table
       person_id: FK → people
       memory_id: FK → memories
       role: str  # subject, mentioned, about
   ```

4. **Set up Alembic** for migrations:
   - `alembic init backend/database/migrations`
   - Configure async driver
   - Create initial migration

5. **Wire database lifespan** into `backend/main.py`:
   - Create tables on startup (dev mode)
   - Close connection pool on shutdown

6. **Add pgvector extension** setup:
   - Migration to `CREATE EXTENSION IF NOT EXISTS vector`

7. **Create indexes**:
   - `memories(user_id, created_at)` — timeline queries
   - `memories(user_id, category)` — category filtering
   - `people(user_id, name)` — person lookup
   - `financial_records(user_id, person_id, status)` — debt queries
   - `memory_embeddings(embedding)` using IVFFlat or HNSW index

## Success Criteria

- [ ] PostgreSQL connects successfully from backend
- [ ] All models create tables via Alembic migration
- [ ] pgvector extension installed and vector column works
- [ ] CRUD operations work for all models (tested)
- [ ] Vector similarity search returns results
- [ ] Connection pooling configured correctly

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|-----------|
| pgvector not available in user's PostgreSQL | Blocks vector search | Provide Docker compose with pgvector image |
| Schema needs changes after data exists | Migration pain | Use Alembic from day one, design for flexibility |
| Vietnamese text in embeddings | Poor search quality | Use multilingual embedding model |
