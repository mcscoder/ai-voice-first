---
title: "Migrate TTS Endpoint To Backend"
description: "Move the working Edge TTS endpoint from TTS-test into the main FastAPI backend without expanding the existing main.py monolith."
status: completed
priority: P2
effort: 6h
issue:
branch: faster-whisper
tags: [feature, backend, api, tts]
blockedBy: []
blocks: []
created: 2026-04-26
---

# Migrate TTS Endpoint To Backend

## Overview

Migrate `POST /tts` from `TTS-test` into `backend`, preserving current behavior: JSON text input, Vietnamese default voice, English option, trimmed text validation, 5000 char cap, 30s synthesis timeout, binary `audio/mpeg` response, and download header.

Implementation complete: backend split into modules, `/tts` wired in, tests passed, and runtime docs already updated.

## Mode

Fast plan. Source and target code are local. No external docs needed.

## Cross-Plan Dependencies

No unfinished root `plans/` directory existed before this plan. No blockers.

## Key Findings

- Source endpoint lives in `TTS-test/main.py`.
- Target backend is FastAPI + `uv` in `backend/main.py`.
- `backend/main.py` is already 256 lines, above project 200-line guidance.
- Backend has no test suite yet.
- Root `README.md`, `CLAUDE.md`, `AGENTS.md`, and `docs/` are absent on disk; instructions were supplied in chat.

## Phases

| Phase | Name | Status |
|-------|------|--------|
| 1 | [Prepare Backend Structure](./phase-01-prepare-backend-structure.md) | Complete |
| 2 | [Port TTS Endpoint](./phase-02-port-tts-endpoint.md) | Complete |
| 3 | [Add Tests And Validation](./phase-03-add-tests-and-validation.md) | Complete |
| 4 | [Update Runtime Documentation](./phase-04-update-runtime-documentation.md) | Complete |

## Dependencies

- Add runtime package: `edge-tts`.
- Add test packages if missing: `pytest`, `httpx`.
- Keep package manager: `uv`.
- Python module filenames should remain importable (`snake_case`) even though repo guidance prefers kebab-case generally.

## Success Criteria

- `POST /tts` works from the main backend app.
- Existing `POST /transcribe` behavior remains unchanged.
- `backend/main.py` becomes app wiring only and stays under 200 lines.
- Tests cover TTS happy paths, validation, OpenAPI binary schema, timeout/empty stream errors, and basic transcribe route preservation.
- `uv run python -m compileall .` passes in `backend`.
- `uv run pytest` passes in `backend`.

## Cook Command

```bash
/ck:cook --auto /home/mcs/Workspaces/ai-voice-first/plans/260426-1631-migrate-tts-endpoint-to-backend/plan.md
```

## Unresolved Questions

None.
