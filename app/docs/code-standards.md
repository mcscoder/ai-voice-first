# Code Standards

## Naming

- Use `snake_case` for files.
- Use `PascalCase` for types.
- Use `camelCase` for variables, methods, and constants.

## Structure

- Put reusable infrastructure in `lib/core/`.
- Put product behavior in `lib/features/`.
- Put shared widgets, forms, and localization helpers in `lib/shared/`.
- Keep routes and dependency registration consistent with the current app shell.

## Generated Files

- Regenerate DI after changing `@injectable`, `@lazySingleton`, `@module`, or related bindings.
- Regenerate localization outputs after editing ARB files.
- Do not hand-edit generated files unless a generator is unavailable and the file must be unblocked immediately.

## Delivery Checks

- `flutter pub get`
- `dart run build_runner build --delete-conflicting-outputs`
- `flutter gen-l10n`
- `flutter analyze`
- `flutter test`
