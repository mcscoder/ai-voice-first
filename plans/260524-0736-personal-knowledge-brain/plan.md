---
title: "Personal Knowledge Brain - Second Brain bằng Giọng Nói"
description: "Transform the voice assistant into a personal knowledge management system with memory graph, personality AI, contextual reminders, fuzzy retrieval, and behavioral reflection."
status: pending
priority: P1
effort: 120h
issue:
branch: feat/knowledge-brain
tags: [feature, flutter, backend, ai, memory, voice, database]
blockedBy: []
blocks: []
created: 2026-05-24
---

# Personal Knowledge Brain

## Overview

Upgrade the current voice assistant from a stateless voice-in/voice-out loop into a **personal knowledge management system** — a "second brain" that understands, organizes, reasons about, and proactively surfaces information from the user's life.

**Current state:** Flutter records audio → Backend transcribes → LLM replies → TTS plays back. No memory, no persistence, no context between sessions.

**Target state:** Every voice interaction feeds into a persistent **Memory Graph**. The AI understands relationships between people, money, events, and emotions. It can recall fuzzy queries ("ai nợ tao tiền?"), generate insights ("Minh nợ nhiều nhất tháng này"), and proactively remind based on context.

## Core Concept Upgrade

| Before | After |
|--------|-------|
| Record → Save → Remind → Replay | **Understand → Organize → Reason → Proactively Help** |
| Stateless Q&A | Persistent memory with reasoning |
| Generic assistant | Personality-driven companion |
| No recall | Fuzzy retrieval + insights |

## Cross-Plan Dependencies

| Relationship | Plan | Status |
|-------------|------|--------|
| Foundation | `260531-1703-memory-rag-context-retrieval` | complete |
| Depends on | `260523-2349-voice-assistant-response-flow` | complete |
| Depends on | `260426-1631-migrate-tts-endpoint-to-backend` | completed |

Voice pipeline, TTS, and the focused SQLite RAG context plan are complete. The broader plan can now continue with deeper graph retrieval, reminders, insights, and UI work without hiding the previous recency-window blocker.

## Architecture Decision

**Database:** PostgreSQL + pgvector for structured data + vector embeddings for semantic search.

**Why PostgreSQL:**
- Memory graph needs relational queries (people, debts, events, relationships)
- pgvector enables semantic/fuzzy retrieval without a separate vector DB
- JSON columns handle flexible metadata
- Mature ecosystem, future-proof

**Memory Processing Pipeline:**
```
Voice Input → Transcription → Memory Extraction (LLM) → Store in Graph
                                                      → Generate Embeddings
                                                      → Link to Existing Memories
```

**Retrieval Pipeline:**
```
User Query → Intent Detection → Semantic Search (pgvector)
                              → Graph Traversal (SQL)
                              → LLM Synthesis → Personality-filtered Response
```

## Phases

| Phase | Name | Status |
|-------|------|--------|
| 1 | [Database & Memory Schema](./phase-01-database-memory-schema.md) | Pending |
| 2 | [Memory Extraction Engine](./phase-02-memory-extraction-engine.md) | Pending |
| 3 | [Memory Graph & Linking](./phase-03-memory-graph-linking.md) | Pending |
| 4 | [Personality System](./phase-04-personality-system.md) | Pending |
| 5 | [Smart Retrieval & Fuzzy Search](./phase-05-smart-retrieval.md) | Pending |
| 6 | [Contextual Reminders](./phase-06-contextual-reminders.md) | Pending |
| 7 | [Reflection & Insights Engine](./phase-07-reflection-insights.md) | Pending |
| 8 | [Flutter UI Overhaul](./phase-08-flutter-ui-overhaul.md) | Pending |
| 9 | [Integration Testing & Polish](./phase-09-integration-testing.md) | Pending |

## Dependencies

- PostgreSQL instance (local dev or Docker)
- pgvector extension
- LLM API for memory extraction (reuse existing assistant provider)
- Sentence embedding model for vector search (all-MiniLM-L6-v2 or multilingual variant)

## Success Criteria

- User speaks naturally → memories auto-categorized and stored
- "Ai nợ tao tiền?" → returns relevant people with amounts
- "Lần cuối gặp Minh khi nào?" → timeline retrieval works
- Personality system changes response tone
- Weekly/monthly recap generated automatically
- Memory graph links people, events, finances, emotions

## Risks

| Risk | Mitigation |
|------|-----------|
| LLM extraction accuracy for Vietnamese | Use bilingual prompts, test with real data, allow user correction |
| Embedding quality for Vietnamese text | Use multilingual model (paraphrase-multilingual-MiniLM-L12-v2) |
| Database latency for graph queries | Index design, query optimization, connection pooling |
| Privacy — all memories stored server-side | Encrypt at rest, user-scoped data, clear deletion path |
| Scope creep across 17+ features | Phased rollout, defer Crazy Ideas to post-MVP |

## Feature Mapping to Phases

| Brainstorm Feature | Phase |
|-------------------|-------|
| A1. Auto-classify memories | Phase 2 |
| A2. Memory Graph (relationships) | Phase 3 |
| A3. Life Timeline | Phase 3 |
| B4. Context-aware reminders | Phase 6 |
| B5. Soft reminders | Phase 6 |
| C6. Personality customization | Phase 4 |
| C7. Memory tone matching | Phase 4 |
| D8. Fuzzy retrieval | Phase 5 |
| D9. Insights | Phase 7 |
| D10. Memory recap | Phase 7 |
| E11. Behavior analysis | Phase 7 |
| E12. Warnings/alerts | Phase 7 |
| E13. Emotional memory | Phase 2, 7 |
| F14–F17. Crazy ideas | Post-MVP |

## Cook Command

```bash
/ck:cook /home/mcs/Workspaces/ai-voice-first/plans/260524-0736-personal-knowledge-brain/plan.md
```

> **Best Practice:** Run `/clear` before implementing to reduce planning-context carryover.
