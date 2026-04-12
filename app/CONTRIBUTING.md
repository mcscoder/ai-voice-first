# Contributing to AI Voice First

## Development Setup

```sh
flutter pub get
dart run build_runner build --delete-conflicting-outputs
flutter gen-l10n
```

## Working Rules

- Keep changes focused and product-specific.
- Update generated files when dependency injection or localization changes.
- Run `flutter analyze` and `flutter test` before opening a PR.

## Commit Style

Use conventional commits such as:

```text
feat: add voice session screen
fix: handle microphone permission denial
docs: update setup guide
```
