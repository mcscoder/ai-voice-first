---
phase: 2
title: "Memory Extraction Engine"
status: pending
priority: P1
effort: "16h"
dependencies: [1]
---

# Phase 2: Memory Extraction Engine

## Overview

Build the LLM-powered pipeline that extracts structured memories from raw transcribed text. When the user says "Minh nợ tao 60k", the system should extract: a person (Minh), a financial record (60,000 VND owed), a category (finance + relationship), and sentiment.

This is the intelligence core — the brainstorm's upgrade from "Ghi lại" to "Hiểu".

## Requirements

### Functional
- Extract structured data from natural Vietnamese/English speech
- Auto-classify memories into categories: finance, work, relationship, plan, emotion, general
- Extract named entities (people, places, amounts, dates)
- Detect sentiment and emotional tone
- Rate importance (1-10 scale)
- Handle bilingual input (Vietnamese primary, English secondary)
- Generate vector embeddings for each memory

### Non-functional
- Extraction latency: < 3 seconds per memory
- Must not block the voice response pipeline
- Graceful degradation if extraction fails (store raw text)

## Architecture

### Processing Pipeline

```
Transcription Text
       ↓
┌──────────────────┐
│ Memory Extractor │ (LLM structured output)
│  - categories    │
│  - entities      │
│  - sentiment     │
│  - importance    │
│  - financial     │
└──────────────────┘
       ↓
┌──────────────────┐
│ Entity Resolver  │ (Match to existing people/entities)
│  - name matching │
│  - alias lookup  │
│  - create new    │
└──────────────────┘
       ↓
┌──────────────────┐
│ Embedding Gen    │ (sentence-transformers)
│  - multilingual  │
│  - store vector  │
└──────────────────┘
       ↓
  Database Write
```

### LLM Extraction Prompt Design

The extraction prompt must handle Vietnamese colloquial speech:
- "Minh nợ 60k" → Person: Minh, Amount: 60,000 VND, Type: debt_owed
- "Mai gặp sếp bàn dự án" → Person: sếp, Category: work, Plan: meeting
- "Mệt quá, ghét làm overtime" → Category: emotion, Sentiment: negative

Output format: structured JSON that maps directly to database models.

## Related Code Files

### Create
- `backend/memory/__init__.py` — Memory package
- `backend/memory/extractor.py` — LLM-based memory extraction
- `backend/memory/entity_resolver.py` — Match/create people entities
- `backend/memory/embedding_service.py` — Vector embedding generation
- `backend/memory/memory_service.py` — Orchestration service
- `backend/memory/schemas.py` — Pydantic models for extraction output
- `backend/memory/prompts.py` — LLM prompt templates

### Modify
- `backend/assistant_routes.py` — Hook memory extraction into voice pipeline
- `backend/assistant_service.py` — Pass conversation context to memory service
- `backend/pyproject.toml` — Add sentence-transformers dependency

## Implementation Steps

1. **Create Pydantic schemas** (`backend/memory/schemas.py`):
   ```python
   class ExtractedEntity(BaseModel):
       name: str
       type: Literal["person", "place", "organization"]
       role: str  # subject, mentioned, about

   class ExtractedFinancial(BaseModel):
       amount: float
       currency: str = "VND"
       type: Literal["debt_owed", "debt_owed_to", "expense", "income"]
       person_name: str | None
       due_date: str | None  # natural language date

   class ExtractedMemory(BaseModel):
       processed_text: str
       category: Literal["finance", "work", "relationship", "plan", "emotion", "general"]
       subcategory: str | None
       entities: list[ExtractedEntity]
       financial: ExtractedFinancial | None
       sentiment: float  # -1.0 to 1.0
       importance: int  # 1-10
       emotional_tags: list[str]  # frustrated, happy, anxious, etc.
       time_references: list[str]  # "yesterday", "next week", etc.
   ```

2. **Build the LLM extractor** (`backend/memory/extractor.py`):
   - Use the existing `VoiceAssistantService` chat completions client
   - System prompt instructs extraction in JSON format
   - Parse response into `ExtractedMemory`
   - Handle extraction failures gracefully (return raw text with "general" category)

3. **Build the entity resolver** (`backend/memory/entity_resolver.py`):
   - Fuzzy name matching against existing `Person` records
   - Alias support ("Minh", "thằng Minh" → same person)
   - Create new person records for unknown entities
   - Update `interaction_count` and `last_interaction_at`

4. **Build the embedding service** (`backend/memory/embedding_service.py`):
   - Load `paraphrase-multilingual-MiniLM-L12-v2` model
   - Generate 384-dim embeddings from processed text
   - Lazy model loading (like Whisper pattern)
   - Store in `MemoryEmbedding` table

5. **Build the orchestration service** (`backend/memory/memory_service.py`):
   - `process_transcript(user_id, raw_text) → Memory`
   - Extract → Resolve entities → Generate embedding → Store all
   - Run as background task (don't block voice response)

6. **Hook into voice pipeline** (`backend/assistant_routes.py`):
   - After successful voice response, fire-and-forget memory extraction
   - Use `asyncio.create_task()` for non-blocking processing
   - Log extraction failures, don't surface to user

## Success Criteria

- [ ] "Minh nợ 60k" extracts: person=Minh, amount=60000, category=finance
- [ ] "Mai gặp sếp" extracts: person=sếp, category=work
- [ ] "Mệt quá" extracts: category=emotion, sentiment < 0
- [ ] Entity resolver matches existing people by alias
- [ ] Embeddings generated and stored for all memories
- [ ] Voice response pipeline not slowed down by extraction
- [ ] Extraction failures logged but don't crash the response

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|-----------|
| LLM JSON output malformed | Extraction fails | Retry with simpler prompt, fallback to raw storage |
| Vietnamese slang parsing | Missed entities | Iterative prompt tuning, user feedback loop |
| Embedding model download size (~500MB) | Slow first start | Lazy loading, Docker layer caching |
| Background task exceptions | Silent data loss | Structured logging, health check endpoint |
