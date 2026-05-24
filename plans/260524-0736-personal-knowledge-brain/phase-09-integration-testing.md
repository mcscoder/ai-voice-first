---
phase: 9
title: "Integration Testing & Polish"
status: pending
priority: P1
effort: "18h"
dependencies: [1, 2, 3, 4, 5, 6, 7, 8]
---

# Phase 9: Integration Testing & Polish

## Overview

End-to-end testing, performance optimization, security hardening, and documentation for the entire system. This phase ensures everything works together as a cohesive product.

## Requirements

### Functional
- Full voice-to-memory pipeline works end-to-end
- All retrieval queries return correct results
- Personality system affects all responses consistently
- Reminders fire at correct times
- Insights generate accurately from real data
- Flutter UI connects to all backend endpoints

### Non-functional
- Voice response latency: < 5 seconds (including memory extraction)
- Search queries: < 1 second
- Database queries: indexed, no N+1 problems
- Memory data encrypted at rest
- User authentication (basic JWT for API access)
- Rate limiting on all endpoints

## Architecture

### Test Matrix

| Layer | Test Type | Tool |
|-------|----------|------|
| Backend models | Unit | pytest |
| Memory extraction | Unit + Integration | pytest |
| Retrieval search | Integration | pytest + test DB |
| API routes | Integration | httpx + pytest |
| Full pipeline | E2E | pytest + real LLM |
| Flutter UI | Widget | flutter_test |
| Flutter API | Unit | mockito |
| Flutter E2E | Integration | integration_test |

## Related Code Files

### Create
- `backend/tests/test_memory_extraction.py` — Memory extraction tests
- `backend/tests/test_retrieval.py` — Search and retrieval tests
- `backend/tests/test_personality.py` — Personality system tests
- `backend/tests/test_reminders.py` — Reminder logic tests
- `backend/tests/test_insights.py` — Insight generation tests
- `backend/tests/test_graph.py` — Memory graph tests
- `backend/tests/conftest.py` — Shared fixtures (test DB, mock LLM)
- `backend/auth/` — JWT authentication module
- `backend/middleware/` — Rate limiting middleware
- `docker-compose.yml` — PostgreSQL + pgvector for local dev
- `docs/ARCHITECTURE.md` — System architecture documentation
- `docs/API.md` — API documentation
- `docs/DEPLOYMENT.md` — Deployment guide

### Modify
- `backend/main.py` — Add auth middleware, rate limiting
- `backend/assistant_routes.py` — Add auth requirement
- `app/lib/core/network/dio.dart` — Add auth token interceptor

## Implementation Steps

### Testing

1. **Backend test infrastructure**:
   - Test PostgreSQL database (use Docker testcontainers or sqlite fallback)
   - Mock LLM service for deterministic extraction tests
   - Test fixtures for users, memories, people, financial records
   - Async test runner setup

2. **Memory pipeline tests**:
   ```python
   # Test extraction
   async def test_extract_financial_memory():
       result = await extractor.extract("Minh nợ tao 60k")
       assert result.category == "finance"
       assert result.financial.amount == 60000
       assert result.entities[0].name == "Minh"

   # Test entity resolution
   async def test_resolve_existing_person():
       # Given person "Minh" exists
       # When "thằng Minh" is mentioned
       # Then resolves to same person
   ```

3. **Retrieval tests**:
   ```python
   async def test_fuzzy_debt_query():
       # Given: 3 memories about different debts
       # When: "ai nợ tao tiền?"
       # Then: returns all debtors with amounts

   async def test_timeline_query():
       # Given: memories across 7 days
       # When: "hôm qua tao làm gì?"
       # Then: returns only yesterday's memories
   ```

4. **Flutter widget tests**:
   - Voice screen with mock cubit states
   - Timeline rendering with mock data
   - Person detail with financial summary
   - Personality picker state transitions

### Security

5. **Add JWT authentication**:
   - Simple JWT-based auth (no OAuth for MVP)
   - `/v1/auth/login` — email/password → JWT
   - `/v1/auth/register` — create account
   - All `/v1/` routes require valid JWT
   - User ID extracted from token for data scoping

6. **Rate limiting**:
   - 30 requests/minute per user for voice endpoints
   - 100 requests/minute for read endpoints
   - 429 Too Many Requests response

7. **Data encryption**:
   - Database-level encryption at rest (PostgreSQL settings)
   - Sensitive fields (raw_text) encryption option
   - Secure env variable management

### Performance

8. **Query optimization**:
   - EXPLAIN ANALYZE on all retrieval queries
   - Ensure indexes cover common access patterns
   - Connection pool tuning (based on load testing)
   - Embedding generation batching

9. **Latency optimization**:
   - Parallel: memory extraction + voice response
   - Cache: frequently accessed person profiles
   - Lazy: embedding model loading

### Documentation

10. **Architecture docs** (`docs/ARCHITECTURE.md`):
    - System overview diagram
    - Data flow for voice → memory → retrieval
    - Technology choices and rationale
    - Database schema ER diagram

11. **API docs** (`docs/API.md`):
    - All endpoints with request/response examples
    - Authentication flow
    - Error codes and handling

12. **Docker setup** (`docker-compose.yml`):
    ```yaml
    services:
      db:
        image: pgvector/pgvector:pg16
        environment:
          POSTGRES_DB: knowledge_brain
          POSTGRES_USER: brain
          POSTGRES_PASSWORD: brain_dev
        ports:
          - "5432:5432"
        volumes:
          - pgdata:/var/lib/postgresql/data

      backend:
        build: ./backend
        depends_on: [db]
        env_file: ./backend/.env
        ports:
          - "8000:8000"
    ```

## Success Criteria

- [ ] Full E2E: speak → extract memory → query memory → get answer
- [ ] All backend tests pass (>80% coverage on new code)
- [ ] Flutter widget tests pass for all new screens
- [ ] JWT auth blocks unauthenticated requests
- [ ] Rate limiting returns 429 on abuse
- [ ] Voice response latency < 5 seconds
- [ ] Search queries < 1 second
- [ ] Docker compose spins up complete stack
- [ ] Architecture and API docs complete

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Test DB setup complexity | Slow CI | Docker testcontainers, parallel test execution |
| Auth adds friction to dev | Slow development | Skip auth in dev mode via env flag |
| Performance regression | Bad UX | Benchmark baseline, alert on degradation |
| Docker image size (Whisper + embeddings) | Slow deploy | Multi-stage builds, model caching |
