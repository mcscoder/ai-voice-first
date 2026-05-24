---
phase: 5
title: "Smart Retrieval & Fuzzy Search"
status: pending
priority: P1
effort: "16h"
dependencies: [1, 2, 3]
---

# Phase 5: Smart Retrieval & Fuzzy Search

## Overview

The brain's most powerful capability: answering vague, fuzzy, natural-language questions by searching across the memory graph. "Hình như có thằng nào nợ tao tiền?" should return Minh and the exact amounts. This implements brainstorm features D8 (Fuzzy retrieval) and the retrieval foundation for all other features.

## Requirements

### Functional
- Fuzzy natural language queries: "ai nợ tao tiền?", "hôm qua tao làm gì?"
- Intent detection: is this a query, a new memory, or a command?
- Hybrid search: semantic (pgvector) + structured (SQL) + graph traversal
- Context-aware responses: inject relevant memories into LLM prompt
- Multi-hop reasoning: "ai nợ nhiều nhất?" requires aggregation

### Non-functional
- Search latency: < 1 second for most queries
- Relevance: top-3 results should contain the answer 90% of the time
- Graceful degradation: if search fails, fall back to generic LLM response

## Architecture

### Query Processing Pipeline

```
User Query (voice transcription)
       ↓
┌──────────────────┐
│ Intent Detector  │ → Is this a query? New memory? Command?
└──────────────────┘
       ↓ (if query)
┌──────────────────┐
│ Query Analyzer   │ → Extract: time range, person, category, keywords
└──────────────────┘
       ↓
┌──────────────────────────────┐
│ Hybrid Search                │
│  ├── Semantic: pgvector      │ → Top-K similar memories
│  ├── Structured: SQL         │ → Filter by person/category/date
│  └── Graph: traversal        │ → Related memories via links
└──────────────────────────────┘
       ↓
┌──────────────────┐
│ Result Ranker    │ → Score and deduplicate results
└──────────────────┘
       ↓
┌──────────────────┐
│ Context Builder  │ → Format memories as LLM context
└──────────────────┘
       ↓
┌──────────────────┐
│ LLM Response     │ → Answer with personality + context
└──────────────────┘
```

### Intent Detection

| Intent | Example | Action |
|--------|---------|--------|
| `query` | "Ai nợ tao tiền?" | Search memories → answer |
| `memory` | "Minh nợ tao 60k" | Store new memory → acknowledge |
| `command` | "Đổi sang toxic mode" | Execute command |
| `conversation` | "Hôm nay trời đẹp nhỉ" | Generic chat (still store as memory) |

## Related Code Files

### Create
- `backend/retrieval/__init__.py` — Retrieval package
- `backend/retrieval/intent_detector.py` — Classify user intent
- `backend/retrieval/query_analyzer.py` — Parse query into search parameters
- `backend/retrieval/search_service.py` — Hybrid search orchestration
- `backend/retrieval/semantic_search.py` — pgvector similarity search
- `backend/retrieval/structured_search.py` — SQL-based filtering
- `backend/retrieval/context_builder.py` — Format results for LLM prompt
- `backend/retrieval/retrieval_routes.py` — API endpoints for search (optional)

### Modify
- `backend/assistant_service.py` — Add memory context to completions
- `backend/assistant_routes.py` — Route queries through retrieval pipeline
- `backend/memory/memory_service.py` — Dual-path: store vs. query

## Implementation Steps

1. **Build intent detector** (`backend/retrieval/intent_detector.py`):
   - LLM-based classification into query/memory/command/conversation
   - Keyword hints for fast detection (question words: ai, gì, khi nào, bao nhiêu, ở đâu)
   - Two-stage: fast keyword check → LLM fallback for ambiguous cases

2. **Build query analyzer** (`backend/retrieval/query_analyzer.py`):
   ```python
   class QueryAnalysis(BaseModel):
       intent: Literal["query", "memory", "command", "conversation"]
       person_names: list[str]  # Extracted names
       time_range: TimeRange | None  # "hôm qua", "tuần trước"
       categories: list[str]  # finance, work, etc.
       keywords: list[str]
       aggregation: str | None  # "nhiều nhất", "tổng cộng"
   ```

3. **Build semantic search** (`backend/retrieval/semantic_search.py`):
   ```python
   async def search_similar(
       user_id: UUID,
       query_text: str,
       top_k: int = 10,
       category_filter: str | None = None,
       time_range: TimeRange | None = None,
   ) -> list[ScoredMemory]:
       # Generate embedding for query
       # pgvector cosine similarity search
       # Apply filters
   ```

4. **Build structured search** (`backend/retrieval/structured_search.py`):
   ```python
   async def search_structured(
       user_id: UUID,
       person_names: list[str] | None = None,
       categories: list[str] | None = None,
       time_range: TimeRange | None = None,
       financial_status: str | None = None,
   ) -> list[Memory]:
       # SQL queries against memories, people, financial_records
       # Join with person_memories for entity filtering
   ```

5. **Build hybrid search orchestrator** (`backend/retrieval/search_service.py`):
   - Run semantic + structured in parallel
   - Merge and deduplicate results
   - Score by: semantic similarity × recency × importance
   - Return top-K results with context

6. **Build context builder** (`backend/retrieval/context_builder.py`):
   - Format retrieved memories as structured context for LLM
   - Include person profiles, financial summaries, relevant history
   - Token-budget aware: trim context to fit model limits
   ```python
   def build_context(memories: list[Memory], people: list[Person]) -> str:
       """
       Format:
       [MEMORY CONTEXT]
       - Minh nợ mày 60k (15/5/2026, chưa trả)
       - Lần cuối gặp Minh: 10/5/2026 ở quán café
       - Minh đã nợ 3 lần trong 2 tháng
       [/MEMORY CONTEXT]
       """
   ```

7. **Integrate into assistant pipeline**:
   - Detect intent before generating response
   - If query → run retrieval → inject context → respond with knowledge
   - If memory → store → respond with acknowledgment
   - If command → route to command handler
   - If conversation → respond normally + store as memory

## Success Criteria

- [ ] "Ai nợ tao tiền?" → returns list of debtors with amounts
- [ ] "Hôm qua tao làm gì?" → timeline of yesterday's memories
- [ ] "Lần cuối gặp Minh?" → correct date and context
- [ ] "Minh nợ tao bao nhiêu?" → exact total amount
- [ ] Intent detection correctly classifies 90%+ of inputs
- [ ] Search results returned in < 1 second
- [ ] Memory context doesn't exceed LLM token limits

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Intent detection misclassifies | Wrong response path | Dual-stage detection, user correction loop |
| Semantic search misses Vietnamese | Poor recall | Multilingual embeddings, fallback to keyword |
| Token budget exceeded with context | LLM error | Smart truncation, relevance-based pruning |
| Aggregation queries are complex | Wrong answers | LLM handles aggregation from context |
