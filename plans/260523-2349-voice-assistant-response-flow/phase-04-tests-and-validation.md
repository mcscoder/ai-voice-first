---
phase: 4
title: "Tests And Validation"
status: complete
priority: P1
effort: 3h
dependencies: [2, 3]
---

# Phase 4: Tests And Validation

## Overview

Add regression coverage for the new assistant flow on both backend and Flutter. The tests
should prove that the client only sends audio, the backend returns assistant replies, and
the sensitive pieces stay server-side.

## Requirements

- Functional:
  - Backend tests cover assistant route success and failure paths.
  - Flutter tests cover assistant reply state and UI rendering.
  - No test should hit the real assistant provider.
- Non-functional:
  - Tests must be deterministic.
  - Do not require a Whisper download in the test path.
  - Keep test fixtures small and readable.

## Architecture

Recommended coverage:

- Backend:
  - route returns assistant text payload
  - prompt assembly uses backend config
  - assistant provider timeout and failure mapping
  - existing transcription route still works
- Flutter:
  - voice screen renders assistant output
  - loading / error states transition correctly
  - API client sends audio and language hint only
  - no transcript text is surfaced in UI assertions

## Related Code Files

- Modify:
  - `backend/tests/*`
  - `backend/pyproject.toml`
  - `app/test/*`
  - `app/pubspec.yaml` if test deps need a change
- Create:
  - backend assistant tests
  - Flutter assistant feature tests

## Implementation Steps

1. Add backend unit tests for assistant orchestration with mocked HTTP client and Whisper service.
2. Add backend route tests for response schema and error mapping.
3. Add Flutter widget and cubit tests for assistant replies.
4. Validate that no test depends on live network or secrets.
5. Run backend compile checks and Flutter analyzer/tests.

## Todo List

- [x] Backend success path tests.
- [x] Backend error path tests.
- [x] Flutter cubit tests.
- [x] Flutter widget tests.
- [x] Compile and analyzer validation.

## Success Criteria

- Tests pass without network access.
- Backend does not require live assistant provider access.
- Flutter tests confirm assistant reply rendering.

## Risk Assessment

- Mocking the assistant provider too loosely can miss request-shape regressions.
- Flutter tests can become brittle if the state model stays unclear.

## Security Considerations

- Tests should not use real confidential prompts or tokens.
- Tests should not print raw transcript text unless it is synthetic and harmless.

## Next Steps

Use the test results to fix any contract drift before writing docs.
