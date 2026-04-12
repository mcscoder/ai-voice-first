# Module Guides

## Core Modules

- `analytics/`: product analytics abstraction
- `cache/`: in-memory and disk-backed caching
- `connectivity/`: online state and offline queue handling
- `firebase/`: Firebase initialization and service wrappers
- `network/`: Dio client and request interceptors
- `permissions/`: runtime permission management
- `router/`: route definitions and router configuration
- `theme/`: shared light and dark theme setup

## Shared Modules

- `forms/`: reusable Formz inputs
- `i18n/`: ARB files and generated localization classes
- `widgets/`: reusable UI building blocks

## Usage Rule

Add product-specific behavior in `lib/features/` first. Move code into `lib/shared/` only when it is reused across multiple features.
