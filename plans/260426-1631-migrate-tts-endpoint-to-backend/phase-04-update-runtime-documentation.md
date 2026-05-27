# Update Runtime Documentation

## Context Links

- [Plan](./plan.md)
- [Backend README](/home/mcs/Workspaces/ai-voice-first/backend/README.md)
- [TTS README Source](/home/mcs/Workspaces/ai-voice-first/TTS-test/README.md)
- [Backend GPU Setup](/home/mcs/Workspaces/ai-voice-first/backend/docs/GPU_SETUP.md)

## Overview

Priority: P2. Status: Completed.

Document the new backend TTS endpoint and update project tracking docs if the implementation creates them.

## Key Insights

- Backend README currently documents only transcription setup.
- TTS source README has clear curl examples and privacy warning.
- Root docs requested by instructions are absent on disk.

## Requirements

- Update backend README with `/tts` request/response examples.
- Preserve transcription run instructions.
- Warn that TTS sends submitted text to remote Edge TTS.
- Warn to add auth/rate limiting before public exposure.
- Mention Swagger UI is not the best MP3 playback test; use `curl --output`.
- If root `docs/` are created during implementation, add changelog/roadmap entries there.

## Architecture

Documentation should stay close to backend runtime:

```text
backend/README.md
backend/docs/GPU_SETUP.md          # unchanged unless cross-link needed
docs/project-changelog.md          # create/update only if root docs adopted
docs/development-roadmap.md        # create/update only if root docs adopted
```

## Related Code Files

- Modify: `/home/mcs/Workspaces/ai-voice-first/backend/README.md`
- Create or modify if implementation adopts root docs:
  - `/home/mcs/Workspaces/ai-voice-first/docs/project-changelog.md`
  - `/home/mcs/Workspaces/ai-voice-first/docs/development-roadmap.md`
  - `/home/mcs/Workspaces/ai-voice-first/docs/codebase-summary.md`
  - `/home/mcs/Workspaces/ai-voice-first/docs/system-architecture.md`

## Implementation Steps

1. Add a TTS API section to backend README.
2. Include Vietnamese and English curl examples.
3. Include validation rules.
4. Include remote-service privacy and reliability notes.
5. Include test commands.
6. If root docs are introduced, update roadmap/changelog with migration status.

## Todo List

- [x] Update backend README run/test section.
- [x] Add `/tts` API docs.
- [x] Add privacy/rate-limit warning.
- [x] Add curl binary-output examples.
- [x] Update root docs only if present or explicitly adopted.

## Success Criteria

- A developer can run backend and call `/tts` from README alone.
- Docs distinguish local ASR transcription from remote Edge TTS synthesis.
- Docs include validation limits and expected output type.

## Risk Assessment

- Risk: docs overstate public-readiness. Mitigation: explicitly call auth/rate limiting out of scope.
- Risk: root docs churn. Mitigation: only create required root docs if implementation scope accepts that convention.

## Security Considerations

- Clearly document remote text transmission.
- Avoid examples with real confidential text.

## Next Steps

Use cook command from plan overview to implement.
