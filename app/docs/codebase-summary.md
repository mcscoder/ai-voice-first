# AI Voice First Codebase Summary

## Overview

`ai-voice-first` is a Flutter application baseline with a neutral product shell and reusable infrastructure modules already wired into app startup.

## Main Structure

```text
lib/
├── app.dart
├── core/      # infrastructure and platform integrations
├── features/  # product-facing screens and flows
└── shared/    # reusable forms, widgets, localization, and models
```

## Current Runtime Shape

- `lib/main.dart`, `lib/main_staging.dart`, and `lib/main_production.dart` select the active flavor.
- `lib/app.dart` initializes Firebase, Hive, HydratedBloc, dependency injection, analytics, cache, connectivity, and global error handlers.
- `lib/core/router/router.dart` exposes a single root route.
- `lib/features/home/home_screen.dart` is a temporary landing screen for the renamed app.

## Reusable Infrastructure

- `core/network/`: Dio client, interceptors, network configuration
- `core/cache/`: memory and disk cache services
- `core/connectivity/`: connectivity state and offline queue support
- `core/firebase/`: Firebase bootstrap and service wrappers
- `core/analytics/`: analytics abstraction
- `core/permissions/`: runtime permission handling
- `core/lifecycle/`: lifecycle observers and update checks
- `core/di/`: `get_it` and generated `injectable` registration
- `core/theme/` and `core/design_system/`: shared theming and tokens

## Removed Template-Specific Runtime Code

- Demo login route
- Demo city model, API, repository, bloc, and cubit
- Auth-gated router redirect logic
- Demo localization strings and widget test
