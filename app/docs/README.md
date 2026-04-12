# AI Voice First Documentation

This documentation set describes the current `ai-voice-first` baseline after template cleanup.

## Read First

1. [project-overview-pdr.md](./project-overview-pdr.md)
2. [codebase-summary.md](./codebase-summary.md)
3. [system-architecture.md](./system-architecture.md)
4. [code-standards.md](./code-standards.md)

## Setup

```sh
flutter pub get
dart run build_runner build --delete-conflicting-outputs
flutter gen-l10n
flutter run -t lib/main.dart
```

## Included Infrastructure

- Routing with `go_router`
- Dependency injection with `get_it` and `injectable`
- Analytics, Firebase, permissions, connectivity, cache, logger, lifecycle, and theme modules under `lib/core/`
- Shared forms, widgets, and localization support under `lib/shared/`

## Current Product State

- Single neutral landing route for `AI Voice First`
- No demo login flow
- No sample city API or repository stack
- Placeholder package and bundle identifier: `com.example.aivoicefirst`
