---
phase: 7
title: "Reflection & Insights Engine"
status: pending
priority: P2
effort: "14h"
dependencies: [1, 2, 3, 5]
---

# Phase 7: Reflection & Insights Engine

## Overview

Build the reflection layer from brainstorm section E: behavior analysis, warnings/alerts, and emotional memory. Also implements D9 (Insights) and D10 (Memory recap). The system should observe patterns in the user's life and generate actionable insights like "Minh nợ 3 lần chưa trả" or "Mày tiêu nhiều hơn tháng trước 40%".

## Requirements

### Functional
- **Behavioral analysis**: Track spending, social patterns, forgotten tasks
- **Financial insights**: Who owes most, spending trends, debt aging
- **Social insights**: Who the user meets most, relationship health
- **Emotional tracking**: Sentiment trends over time
- **Weekly/monthly recaps**: Automated summary generation
- **Proactive warnings**: Alert about concerning patterns

### Non-functional
- Recap generation: < 10 seconds (background, not real-time)
- Insights should be generated periodically (daily/weekly)
- Data privacy: insights never leave the user's scope

## Architecture

### Insight Pipeline

```
Scheduled Job (daily/weekly)
       ↓
┌──────────────────────────┐
│ Data Aggregation         │
│  ├── Financial summary   │
│  ├── Social interactions │
│  ├── Emotional trends    │
│  └── Pattern detection   │
└──────────────────────────┘
       ↓
┌──────────────────────────┐
│ LLM Insight Generation   │ → Natural language insights
└──────────────────────────┘
       ↓
┌──────────────────────────┐
│ Store & Notify           │ → Save insights, push if important
└──────────────────────────┘
```

### Insight Categories

| Category | Examples |
|----------|---------|
| Financial | "Minh nợ nhiều nhất tháng này: 3 lần, tổng 180k" |
| Social | "Mày gặp Minh 5 lần tuần này, nhiều hơn bình thường" |
| Emotional | "Mày hay stressed vào thứ 2, có thể do meetings" |
| Behavioral | "Mày tiêu 2 triệu tuần này, cao hơn trung bình 30%" |
| Warning | "Minh nợ 3 lần chưa trả — nên dừng cho vay" |

## Related Code Files

### Create
- `backend/insights/__init__.py` — Insights package
- `backend/insights/aggregator.py` — Data aggregation queries
- `backend/insights/insight_generator.py` — LLM-based insight creation
- `backend/insights/recap_service.py` — Weekly/monthly recap builder
- `backend/insights/pattern_detector.py` — Behavioral pattern detection
- `backend/insights/emotional_tracker.py` — Sentiment trend analysis
- `backend/insights/insight_routes.py` — API for insights/recaps
- `backend/insights/scheduler.py` — Background job scheduling

### Modify
- `backend/database/models.py` — Add Insight model
- `backend/main.py` — Register insight scheduler

## Implementation Steps

1. **Create Insight model**:
   ```python
   class Insight(Base):
       id: UUID (PK)
       user_id: FK → users
       category: Enum (financial, social, emotional, behavioral, warning)
       title: str  # Short headline
       description: str  # Full insight text
       severity: Enum (info, notable, warning, critical)
       data: JSONB  # Raw aggregated data backing the insight
       period_start: date
       period_end: date
       acknowledged: bool = False
       created_at
   ```

2. **Build data aggregator** (`backend/insights/aggregator.py`):
   ```python
   class InsightAggregator:
       async def financial_summary(user_id, period) -> FinancialAggregation:
           """Total debts, top debtors, spending trends, settlement rate."""

       async def social_summary(user_id, period) -> SocialAggregation:
           """Top contacts, interaction frequency, new people met."""

       async def emotional_summary(user_id, period) -> EmotionalAggregation:
           """Average sentiment, trend, emotional distribution by day."""

       async def behavioral_summary(user_id, period) -> BehavioralAggregation:
           """Category distribution, time patterns, repeated topics."""
   ```

3. **Build pattern detector** (`backend/insights/pattern_detector.py`):
   - Detect: repeated debts from same person
   - Detect: emotional dips on specific days
   - Detect: spending spikes vs average
   - Detect: forgotten follow-ups (mentioned plans never completed)
   - Simple statistical rules, not ML (KISS principle)

4. **Build emotional tracker** (`backend/insights/emotional_tracker.py`):
   - Aggregate sentiment scores from memories
   - Track trend: improving, stable, declining
   - Correlate with categories (work stress, relationship issues)
   - Generate emotional memory insights ("Mày có vẻ không thích Minh")

5. **Build recap service** (`backend/insights/recap_service.py`):
   ```python
   class RecapService:
       async def generate_weekly_recap(user_id) -> Recap:
           """
           Combines: financial, social, emotional, behavioral summaries
           Uses LLM to generate natural-language summary
           Personality-aware tone
           """

       async def generate_monthly_recap(user_id) -> Recap:
           """Longer-term patterns, month-over-month comparison."""
   ```

6. **Build insight generator** (`backend/insights/insight_generator.py`):
   - Take aggregated data → generate natural-language insights via LLM
   - Personality-aware (toxic mode: "Minh nợ hoài à? Đm quá trời luôn!")
   - Prioritize by severity: critical warnings first
   - Deduplicate: don't repeat last week's insight if unchanged

7. **Build scheduler** (`backend/insights/scheduler.py`):
   - Daily job: check for warning-level patterns
   - Weekly job: generate weekly recap + insights
   - Monthly job: generate monthly recap
   - Use asyncio background tasks (same pattern as reminders)

8. **Create API endpoints** (`backend/insights/insight_routes.py`):
   - `GET /v1/insights` — List recent insights
   - `GET /v1/insights/recap/weekly` — Get current week recap
   - `GET /v1/insights/recap/monthly` — Get current month recap
   - `POST /v1/insights/{id}/acknowledge` — Mark as read

## Success Criteria

- [ ] "Minh nợ 3 lần chưa trả" warning generated automatically
- [ ] Weekly recap includes financial, social, emotional summaries
- [ ] Emotional tracker detects sentiment trends by day of week
- [ ] Pattern detector catches repeated debts from same person
- [ ] Insights respect active personality tone
- [ ] Critical warnings delivered via push notification
- [ ] Recaps available on demand via voice query

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Too many insights = information overload | User ignores all | Severity-based filtering, max 3 per day |
| LLM generates incorrect insights | Wrong decisions | Always show raw data backing, allow dismissal |
| Background jobs fail silently | No insights | Health check, retry logic, error logging |
| Emotional tracking feels creepy | User discomfort | Opt-in, transparent about what's tracked |
