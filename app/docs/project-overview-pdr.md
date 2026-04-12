# Project Overview

## Purpose

AI Voice First is the application baseline for a voice-first product. The repository now starts from a neutral shell instead of a sample feature set.

## Current Goals

- Keep the reusable infrastructure modules operational.
- Keep startup, routing, and flavor selection stable.
- Provide a clean base for product-specific voice capture, transcript, and orchestration flows.

## Current Defaults

- Package name: `ai_voice_first`
- Display name: `AI Voice First`
- Placeholder identifier: `com.example.aivoicefirst`
- Root route: `/`

## Near-Term Product Work

- Replace the landing screen with the first real voice interaction flow.
- Define product data models and API integrations under `lib/features/` and `lib/shared/`.
- Keep documentation aligned with the implemented runtime shape.
