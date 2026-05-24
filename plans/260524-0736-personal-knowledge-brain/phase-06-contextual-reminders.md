---
phase: 6
title: "Contextual Reminders"
status: pending
priority: P2
effort: "12h"
dependencies: [1, 2, 3, 5]
---

# Phase 6: Contextual Reminders

## Overview

Implement brainstorm features B4 (Context-aware reminders) and B5 (Soft reminders). The app should proactively surface relevant information based on context — not just time-based alarms, but intelligent nudges like "Gặp Minh → Nó nợ mày 60k" or "Hôm nay thứ 2 rồi đó...".

## Requirements

### Functional
- **Person-triggered reminders**: When user mentions someone → surface relevant context
- **Time-triggered reminders**: Periodic soft nudges (daily/weekly)
- **Pattern-triggered reminders**: Detect recurring behaviors ("Lại quên deadline nữa rồi")
- **Explicit reminders**: User says "nhắc tao..." → create scheduled reminder
- Reminder delivery via push notification + in-app voice

### Non-functional
- Reminder check latency: < 500ms per voice interaction
- Push notifications via Firebase Cloud Messaging (already in pubspec)
- Background processing for scheduled reminders

## Architecture

### Reminder Types

| Type | Trigger | Example |
|------|---------|---------|
| `person_context` | Mentioning a person | "Gặp Minh" → "Nó nợ mày 60k" |
| `time_scheduled` | Explicit time request | "Nhắc tao gọi Minh lúc 3h" |
| `soft_nudge` | Periodic check | "Hôm nay thứ 2, tuần trước mày plan gì rồi?" |
| `debt_reminder` | Unpaid debt aging | "Minh nợ 3 lần chưa trả kìa" |
| `pattern_alert` | Recurring behavior | "Mày lại skip gym rồi" |

### Processing Flow

```
Voice Input → Transcription → Entity Extraction
                                     ↓
                              Person mentioned?
                              ┌──── Yes ────┐
                              ↓             ↓
                        Query person    Check reminders
                        context         for this person
                              ↓             ↓
                        Inject into     Append to
                        LLM prompt      response
```

## Related Code Files

### Create
- `backend/reminders/__init__.py` — Reminders package
- `backend/reminders/reminder_service.py` — Core reminder logic
- `backend/reminders/context_trigger.py` — Person/location context triggers
- `backend/reminders/scheduler.py` — Scheduled reminder processing
- `backend/reminders/nudge_generator.py` — Soft nudge generation
- `backend/reminders/reminder_routes.py` — API for reminder management
- `backend/reminders/push_service.py` — Firebase push notification sender

### Modify
- `backend/assistant_routes.py` — Check context triggers during voice flow
- `backend/assistant_service.py` — Include reminder context in prompt
- `backend/database/models.py` — Reminder model (if not in Phase 1)

## Implementation Steps

1. **Create Reminder model** (if not done in Phase 1):
   ```python
   class Reminder(Base):
       id: UUID (PK)
       user_id: FK → users
       memory_id: FK → memories (nullable)
       person_id: FK → people (nullable)
       type: Enum (person_context, time_scheduled, soft_nudge, debt_reminder, pattern_alert)
       trigger_condition: JSONB  # Flexible trigger rules
       message: str
       scheduled_at: timestamp (nullable)
       delivered: bool
       created_at
   ```

2. **Build context trigger** (`backend/reminders/context_trigger.py`):
   - On each voice interaction, check if mentioned people have pending context
   - Pull: unpaid debts, recent memories, relationship notes
   - Format as concise context for LLM to weave into response
   - Priority: debts > recent events > general context

3. **Build explicit reminder parser**:
   - Detect "nhắc tao", "remind me", "đừng quên" patterns
   - Extract: what, when, who (if applicable)
   - Create scheduled reminder in database
   - Confirm: "Ok, sẽ nhắc mày lúc 3h chiều nay"

4. **Build soft nudge generator** (`backend/reminders/nudge_generator.py`):
   - Daily check: outstanding debts, upcoming plans, forgotten tasks
   - Weekly recap trigger
   - Personality-aware phrasing ("Hôm nay thứ 2 rồi đó....." vs "Monday check-in")

5. **Build push notification service** (`backend/reminders/push_service.py`):
   - Use Firebase Cloud Messaging (already in Flutter dependencies)
   - Register device tokens from Flutter
   - Send notifications for scheduled reminders
   - Notification payload includes reminder context for quick voice follow-up

6. **Build scheduler** (`backend/reminders/scheduler.py`):
   - Background task (asyncio) to check scheduled reminders
   - Run every minute, check for due reminders
   - Fire push notification + mark as delivered
   - Respect user's timezone

7. **Integrate into voice pipeline**:
   - After entity extraction, query context triggers
   - Append relevant context to LLM system prompt
   - LLM naturally includes reminder info in response

## Success Criteria

- [ ] Mentioning "Minh" triggers context about Minh's debts
- [ ] "Nhắc tao gọi Minh lúc 3h" creates a scheduled reminder
- [ ] Scheduled reminder fires push notification at the right time
- [ ] Soft nudges generated for Monday mornings with weekly context
- [ ] Debt aging alerts fire for overdue debts
- [ ] Reminders respect personality tone

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Too many context triggers = annoying | User disables feature | Frequency throttling, importance threshold |
| Push notification permission denied | No scheduled reminders | Graceful fallback to in-app voice delivery |
| Timezone handling bugs | Wrong reminder times | Use UTC internally, convert at delivery |
| NLP date parsing unreliable for Vietnamese | Wrong schedule | Use LLM for date extraction, confirm with user |
