# Quick Start Guide

## Prerequisites

- Flutter SDK compatible with the version declared in `pubspec.yaml`
- Dart SDK compatible with the version declared in `pubspec.yaml`

## Steps

1. Install dependencies:
   ```sh
   flutter pub get
   ```
2. Regenerate code:
   ```sh
   dart run build_runner build --delete-conflicting-outputs
   flutter gen-l10n
   ```
3. Start the default flavor:
   ```sh
   flutter run -t lib/main.dart
   ```

## First Product Edit

- Replace the neutral content in `lib/features/home/home_screen.dart`.
- Add new feature modules under `lib/features/`.
- Keep shared infrastructure in `lib/core/`.
