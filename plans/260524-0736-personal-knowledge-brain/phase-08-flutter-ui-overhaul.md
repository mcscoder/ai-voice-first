---
phase: 8
title: "Flutter UI Overhaul"
status: pending
priority: P1
effort: "18h"
dependencies: [4, 5, 6, 7]
---

# Phase 8: Flutter UI Overhaul

## Overview

Transform the Flutter app from a single-screen voice recorder into a full-featured personal knowledge companion. Add memory timeline, person profiles, insight cards, personality switcher, and reminder management — all while keeping voice-first as the primary interaction paradigm.

## Requirements

### Functional
- **Voice screen upgrade**: Show memory context and active personality
- **Memory timeline**: Scrollable timeline of memories with category icons
- **Person profiles**: View all memories/debts related to a person
- **Insights dashboard**: Card-based layout of recent insights and recaps
- **Personality picker**: Switch personality via UI toggle
- **Reminder management**: View pending, create new reminders
- **Settings**: Backend URL, notification preferences, data management

### Non-functional
- Smooth 60fps animations
- Dark mode support (already in place via AppTheme)
- Responsive layout (phones + tablets)
- Offline indicator (already has ConnectivityCubit)

## Architecture

### New Feature Modules (following existing Clean Architecture pattern)

```
lib/features/
├── voice/          # Existing — upgrade
├── home/           # Existing — replace with dashboard
├── timeline/       # NEW — memory timeline
├── people/         # NEW — person profiles
├── insights/       # NEW — insights & recaps
├── personality/    # NEW — personality management
├── reminders/      # NEW — reminder list
└── settings/       # NEW — app settings
```

### Navigation (using existing go_router)

```
/                   → Dashboard (voice + recent insights)
/voice              → Full voice screen
/timeline           → Memory timeline
/people             → People list
/people/:id         → Person detail
/insights           → Insights dashboard
/insights/recap     → Weekly/monthly recap
/reminders          → Reminder list
/settings           → App settings
/settings/personality → Personality picker
```

## Related Code Files

### Create
- `app/lib/features/timeline/` — Timeline feature module
  - `data/timeline_api.dart` — API client for memories
  - `presentation/timeline_screen.dart` — Timeline UI
  - `presentation/timeline_cubit.dart` — State management
  - `presentation/memory_card.dart` — Memory card widget
- `app/lib/features/people/` — People feature module
  - `data/people_api.dart` — API client for people
  - `presentation/people_list_screen.dart` — People grid/list
  - `presentation/person_detail_screen.dart` — Person profile
  - `presentation/people_cubit.dart` — State management
- `app/lib/features/insights/` — Insights feature module
  - `data/insights_api.dart` — API client for insights
  - `presentation/insights_screen.dart` — Insights dashboard
  - `presentation/recap_screen.dart` — Recap detail view
  - `presentation/insights_cubit.dart` — State management
- `app/lib/features/personality/` — Personality feature module
  - `data/personality_api.dart` — API client
  - `presentation/personality_picker.dart` — Personality UI
  - `presentation/personality_cubit.dart` — State management
- `app/lib/features/reminders/` — Reminders feature module
  - `data/reminders_api.dart` — API client
  - `presentation/reminders_screen.dart` — Reminder list
  - `presentation/reminders_cubit.dart` — State management
- `app/lib/features/settings/` — Settings feature module

### Modify
- `app/lib/features/home/home_screen.dart` — Replace with dashboard
- `app/lib/features/voice/presentation/voice_screen.dart` — Add context display
- `app/lib/core/router/router.dart` — Add new routes
- `app/lib/core/network/api_path.dart` — Add new API paths
- `app/lib/core/design_system/` — Add new design tokens

## Implementation Steps

1. **Dashboard (home screen replacement)**:
   - Large voice button (center, primary CTA)
   - Active personality indicator (top-right badge)
   - Recent insights cards (horizontal scroll)
   - Quick memory count stats
   - Bottom navigation: Voice, Timeline, People, Insights

2. **Voice screen upgrade**:
   - Show current personality avatar/label
   - After response, show extracted memory preview
   - "This was saved as: Finance • Minh nợ 60k"
   - Swipe down to see full memory context

3. **Memory timeline screen**:
   - Vertical scrollable timeline with date headers
   - Each memory: category icon, processed text, entities, time
   - Filter by category (chips at top)
   - Search bar for fuzzy search
   - Pull to refresh

4. **People screen**:
   - Grid of person cards with avatar (initial-based), name, last interaction
   - Trust score indicator (color-coded)
   - Tap → Person detail: all memories, financial summary, interaction timeline
   - Financial records with status (pending/settled)

5. **Insights dashboard**:
   - Card-based layout with severity-colored borders
   - Weekly recap card with expandable detail
   - Category tabs: All, Financial, Social, Emotional
   - Swipe to acknowledge/dismiss

6. **Personality picker**:
   - 4 personality cards with name, description, example response
   - Current selection highlighted
   - Tap to switch with confirmation dialog
   - Preview: "Try me" button that generates sample response

7. **Bottom navigation**:
   ```dart
   BottomNavigationBar(
     items: [
       BottomNavigationBarItem(icon: Icons.mic, label: 'Voice'),
       BottomNavigationBarItem(icon: Icons.timeline, label: 'Timeline'),
       BottomNavigationBarItem(icon: Icons.people, label: 'People'),
       BottomNavigationBarItem(icon: Icons.insights, label: 'Insights'),
     ],
   )
   ```

8. **API clients** — Follow existing `TranscriptionApi` pattern:
   - Each feature gets its own API class extending `Api`
   - Use existing Dio setup with interceptors
   - Add new paths to `api_path.dart`

9. **State management** — Follow existing BLoC/Cubit pattern:
   - Each feature gets its own Cubit
   - Use `@injectable` for DI registration
   - HydratedCubit for persistent state where needed

## Success Criteria

- [ ] Dashboard shows voice button + recent insights + personality indicator
- [ ] Timeline displays chronological memories with category filtering
- [ ] Person detail shows complete memory and financial history
- [ ] Insights cards render with severity colors and actions
- [ ] Personality picker switches personality and shows confirmation
- [ ] Bottom navigation works across all screens
- [ ] Dark mode renders correctly on all new screens
- [ ] All screens follow existing design system tokens

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Too many screens for MVP | Scope creep | Ship voice + timeline + people first, insights later |
| API calls too frequent | Battery drain | Pagination, caching with existing CacheManager |
| Complex navigation state | Bugs | Use go_router's existing patterns, test routes |
| UI inconsistency | Poor UX | Reuse existing design system and shared widgets |
