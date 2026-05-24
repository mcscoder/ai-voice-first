---
phase: 4
title: "Personality System"
status: pending
priority: P2
effort: "10h"
dependencies: [1]
---

# Phase 4: Personality System

## Overview

Implement the AI personality layer from brainstorm features C6 (Personality customization) and C7 (Memory tone matching). The assistant should feel like a real person — not a generic AI. Users can choose between personalities like "Chill", "Toxic nhẹ", "Nghiêm túc", or "Bạn thân mất dạy".

## Requirements

### Functional
- 4 personality presets: chill, mildly_toxic, serious, chaotic_bestie
- Personality affects system prompt, response tone, emoji usage, vocabulary
- Tone matching: adapt to user's speaking patterns over time
- Per-user personality storage (persisted across sessions)
- Personality can be switched via voice command

### Non-functional
- Personality switch takes effect immediately (next response)
- No additional LLM calls for personality — it's prompt engineering
- Tone analysis piggybacks on memory extraction (no extra cost)

## Architecture

### Personality as Prompt Engineering

```
Base System Prompt
       +
Personality Prompt Fragment
       +
Memory Context (what the AI knows about the user)
       +
Conversation Tone Profile
       =
Final System Prompt sent to LLM
```

### Personality Definitions

| Personality | Vietnamese Name | Tone | Example Response |
|-------------|----------------|------|-----------------|
| `chill` | Chill | Relaxed, friendly | "Ờ, Minh nợ mày 60k nè. Từ từ đòi." |
| `mildly_toxic` | Toxic nhẹ | Sarcastic, playful roast | "Minh nợ 60k? Thằng đó nợ hoài không trả, quen rồi." |
| `serious` | Nghiêm túc | Professional, concise | "Minh hiện đang nợ bạn 60,000đ từ ngày 15/5." |
| `chaotic_bestie` | Bạn thân mất dạy | Chaotic, brutally honest | "ĐM Minh nợ 60k chưa trả?! Đòi liền đi bro!" |

## Related Code Files

### Create
- `backend/personality/__init__.py` — Personality package
- `backend/personality/personality_service.py` — Personality management
- `backend/personality/prompt_builder.py` — Build system prompts with personality
- `backend/personality/tone_analyzer.py` — Analyze user's speaking tone
- `backend/personality/presets.py` — Personality preset definitions

### Modify
- `backend/assistant_service.py` — Use personality-aware prompt builder
- `backend/assistant_routes.py` — Accept personality parameter
- `backend/database/models.py` — Add PersonalitySettings model (if not in Phase 1)

## Implementation Steps

1. **Define personality presets** (`backend/personality/presets.py`):
   ```python
   PERSONALITIES = {
       "chill": {
           "name": "Chill",
           "system_prompt_fragment": """
           You are a chill, relaxed friend. Talk casually, use simple language.
           Don't be overly formal. Use occasional Vietnamese slang.
           Emoji: sometimes. Exclamation marks: rarely.
           """,
           "response_style": "casual",
           "emoji_frequency": "low",
       },
       "mildly_toxic": {
           "name": "Toxic nhẹ",
           "system_prompt_fragment": """
           You are a sarcastic friend who loves light roasting. Be playful,
           slightly mocking, but never actually mean. Use irony.
           Point out patterns in a funny way ("lại nợ nữa rồi").
           """,
           "response_style": "sarcastic",
           "emoji_frequency": "medium",
       },
       # ... serious, chaotic_bestie
   }
   ```

2. **Build the prompt builder** (`backend/personality/prompt_builder.py`):
   ```python
   class PersonalityPromptBuilder:
       def build_system_prompt(
           self,
           personality: str,
           language: str,
           memory_context: str | None = None,
           user_tone_profile: dict | None = None,
       ) -> str:
           """Compose final system prompt from personality + context + tone."""
   ```
   - Combines base assistant instructions + personality fragment + memory context
   - Injects relevant memories as context for the LLM

3. **Build tone analyzer** (`backend/personality/tone_analyzer.py`):
   - Track patterns: emoji usage, swearing frequency, formality level
   - Update per-user profile after each interaction
   - Stored in `personality_settings.tone_profile` JSONB column
   - Lightweight: count-based analysis, no extra LLM call

4. **Integrate with assistant service** (`backend/assistant_service.py`):
   - Replace static system prompt with personality-built prompt
   - Accept `personality` parameter from route
   - Inject memory context (from Phase 5 retrieval) into prompt

5. **Voice command detection**:
   - Detect phrases like "đổi personality", "nói toxic đi", "nghiêm túc lại"
   - Route to personality switch instead of normal response
   - Confirm switch: "Ok, toxic mode activated 😈"

## Success Criteria

- [ ] Each personality produces distinctly different response tones
- [ ] Personality persists across sessions (database-backed)
- [ ] Voice command switches personality
- [ ] Tone analyzer tracks user speaking patterns
- [ ] Memory context injected into personality prompts
- [ ] Vietnamese slang/informal speech handled naturally

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|-----------|
| "Toxic" personality goes too far | User offense | Clear guardrails in prompt, avoid personal attacks |
| Personality prompt too long | Token waste, slow | Keep fragments concise (< 200 tokens) |
| Voice command detection false positives | Accidental switch | Require confirmation for personality changes |
