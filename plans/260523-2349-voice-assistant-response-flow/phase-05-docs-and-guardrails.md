---
phase: 5
title: "Docs And Guardrails"
status: complete
priority: P2
effort: 2h
dependencies: [2, 3, 4]
---

# Phase 5: Docs And Guardrails

## Overview

Update runtime documentation so the new assistant flow is discoverable and the privacy
boundary is explicit. The docs should tell engineers that Flutter is only a thin client and
the backend is responsible for transcription, prompting, and provider access.

## Requirements

- Functional:
  - Document the new assistant request flow and endpoint.
  - Document required backend env vars.
  - Document the privacy and rate-limit caveats.
  - Keep the existing transcription docs accurate if they still exist.
- Non-functional:
  - Keep docs aligned with the implemented runtime shape.
  - Avoid overpromising production readiness.

## Architecture

Docs to update should cover:

- backend runtime usage
- backend assistant endpoint examples
- app setup notes that explain the client is thin
- operational warnings for secrets, prompt control, and public exposure

## Related Code Files

- Modify:
  - `backend/README.md`
  - `backend/.env.example`
  - `app/README.md`
  - `app/docs/development-roadmap.md`
  - `app/docs/system-architecture.md`

## Implementation Steps

1. Document the new assistant endpoint with request and response examples.
2. Document the backend-only env vars for assistant provider access.
3. Document that Flutter sends audio only and does not own prompt logic.
4. Document privacy, abuse, and timeout caveats.
5. Update app architecture docs to reflect the assistant response flow.

## Todo List

- [x] Update backend README.
- [x] Update env example.
- [x] Update app docs.
- [x] Add rollout / guardrail notes.

## Success Criteria

- A developer can understand the assistant flow from the docs alone.
- The docs clearly state that sensitive processing stays in backend.
- The docs do not claim public readiness without auth and rate limiting.

## Risk Assessment

- Docs can drift if they are not updated alongside the code.
- If the privacy boundary is not stated clearly, people will misuse the flow.

## Security Considerations

- Call out backend-only secrets and prompt ownership.
- Warn that raw voice input and transcript text are sensitive.

## Next Steps

Ship docs together with the code so the rollout notes match reality.
