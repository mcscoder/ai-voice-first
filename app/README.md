# AI Voice First

Voice-first Flutter application baseline with prewired infrastructure for networking, analytics, connectivity, permissions, theming, dependency injection, and localization.

## Setup

```sh
flutter pub get
dart run build_runner build --delete-conflicting-outputs
flutter gen-l10n
flutter run -t lib/main.dart
```

## Current App Shell

- Root route only: `/`
- Neutral landing screen in `lib/features/home/home_screen.dart`
- Multi-flavor entrypoints in `lib/main.dart`, `lib/main_staging.dart`, and `lib/main_production.dart`

## Project Structure

```text
lib/
├── app.dart
├── core/        # Shared infrastructure
├── features/    # Product features
└── shared/      # Reusable app-level code
```

## Working Baseline

- `lib/core/` keeps the reusable platform and app infrastructure.
- Demo login, sample city data flow, and template branding have been removed.
- Platform names now target `AI Voice First` with placeholder identifier `com.example.aivoicefirst`.

## Docs

- [docs/README.md](./docs/README.md)
- [docs/project-overview-pdr.md](./docs/project-overview-pdr.md)
- [docs/system-architecture.md](./docs/system-architecture.md)
- [docs/codebase-summary.md](./docs/codebase-summary.md)

## License

[MIT](./LICENSE)
