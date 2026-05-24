---
phase: 3
title: "Memory Graph & Linking"
status: pending
priority: P1
effort: "14h"
dependencies: [1, 2]
---

# Phase 3: Memory Graph & Linking

## Overview

Build the memory graph that connects memories to each other, creating a web of relationships. When the user mentions Minh borrowing money, the system links it to previous mentions of Minh, previous loans, and the places/events where they met. This implements brainstorm features A2 (Memory Graph) and A3 (Life Timeline).

## Requirements

### Functional
- Auto-link new memories to related existing memories
- Build person relationship graph (who knows whom, interaction history)
- Track financial relationships over time (borrowing patterns)
- Generate life timeline queries (weekly, monthly, per-person)
- Compute trust/reliability scores from interaction patterns

### Non-functional
- Graph traversal: < 200ms for 2-hop neighbor queries
- Timeline queries: < 300ms for 30-day window
- Link creation should not block response pipeline

## Architecture

### Graph Structure

```
Memory A ──related──→ Memory B
    │                    │
    └──about──→ Person X ←──about──┘
                    │
              FinancialRecord
                    │
              3 loans in 2 months
                    │
              trust_score: 0.3
```

### Link Types

| Type | Description | Example |
|------|------------|---------|
| `related` | Topically similar | Both about work meetings |
| `follows` | Temporal sequence | "Gặp Minh" → "Minh nợ 60k" |
| `updates` | Supersedes previous | "Minh trả 30k" updates "Minh nợ 60k" |
| `contradicts` | Conflicting info | "Minh nói sẽ trả" vs "Minh không trả" |

## Related Code Files

### Create
- `backend/memory/graph_service.py` — Memory graph operations
- `backend/memory/timeline_service.py` — Timeline queries
- `backend/memory/link_builder.py` — Auto-link logic using embeddings + rules
- `backend/memory/trust_scorer.py` — Compute person trust/reliability scores

### Modify
- `backend/memory/memory_service.py` — Add graph linking after memory creation
- `backend/database/models.py` — Add computed fields, indexes

## Implementation Steps

1. **Build the link builder** (`backend/memory/link_builder.py`):
   - **Semantic linking:** Find top-5 similar memories via pgvector cosine similarity
   - **Entity linking:** Auto-link memories mentioning the same person
   - **Temporal linking:** Link memories within same time window (1 hour)
   - **Financial linking:** Link debt/payment memories for the same person
   - Threshold: only create links with similarity > 0.7

2. **Build the graph service** (`backend/memory/graph_service.py`):
   ```python
   class MemoryGraphService:
       async def get_person_context(user_id, person_id) → PersonContext:
           """All memories, financial records, and interaction history for a person."""

       async def get_related_memories(memory_id, depth=2) → list[Memory]:
           """Traverse graph to find connected memories."""

       async def get_financial_summary(user_id, person_id=None) → FinancialSummary:
           """Who owes what, total debts, settlement history."""

       async def get_person_network(user_id) → list[PersonNode]:
           """All people the user has mentioned with relationship strength."""
   ```

3. **Build the timeline service** (`backend/memory/timeline_service.py`):
   ```python
   class TimelineService:
       async def get_timeline(user_id, start, end) → list[MemoryWithContext]:
           """Chronological memories with linked context."""

       async def get_last_interaction(user_id, person_id) → Memory | None:
           """When did the user last mention this person?"""

       async def get_weekly_recap(user_id) → WeeklyRecap:
           """Summary of the past week's memories."""

       async def get_monthly_recap(user_id) → MonthlyRecap:
           """Summary of the past month's memories."""
   ```

4. **Build the trust scorer** (`backend/memory/trust_scorer.py`):
   - Formula based on: debt repayment rate, interaction frequency, sentiment trend
   - Update after each relevant memory
   - Score range: 0.0 (toxic) to 1.0 (highly reliable)
   - Example: Minh borrowed 3 times, repaid 0 → trust_score = 0.2

5. **Integrate into memory pipeline** (`backend/memory/memory_service.py`):
   - After memory creation + embedding, run link_builder
   - After entity resolution, update trust scores
   - After financial record creation, update financial links

6. **Optimize queries** with proper indexes:
   ```sql
   CREATE INDEX idx_memory_links_source ON memory_links(source_memory_id);
   CREATE INDEX idx_memory_links_target ON memory_links(target_memory_id);
   CREATE INDEX idx_person_memory_person ON person_memories(person_id);
   CREATE INDEX idx_person_memory_memory ON person_memories(memory_id);
   CREATE INDEX idx_financial_person_status ON financial_records(user_id, person_id, status);
   ```

## Success Criteria

- [ ] New memory auto-links to semantically similar existing memories
- [ ] Person context query returns full history for a named person
- [ ] Financial summary correctly totals debts across multiple memories
- [ ] Timeline query returns chronological memories for a date range
- [ ] "Lần cuối gặp Minh" returns correct last interaction
- [ ] Trust score updates after debt-related memories
- [ ] Graph traversal stays under 200ms for typical queries

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Too many auto-links (noise) | Graph becomes useless | Similarity threshold tuning, link pruning |
| Graph queries get slow at scale | Bad UX | Proper indexing, limit traversal depth |
| Trust score formula unfair | User confusion | Make transparent, allow user override |
