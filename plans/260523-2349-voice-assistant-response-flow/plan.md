---
title: "Voice Assistant Response Flow"
description: "Replace the transcript-only voice flow with a backend-orchestrated assistant speech flow. Flutter only records and uploads audio, backend handles transcription, prompt assembly, chat completion, and TTS, and the app plays the assistant reply."
status: complete
priority: P1
effort: 18h
issue:
branch: asr-gipformer
tags: [feature, flutter, backend, voice, assistant, api]
blockedBy: []
blocks: []
created: 2026-05-23
---

# Voice Assistant Response Flow

## Overview

Turn the current voice screen from "speech to text" into "speech to assistant speech".
The Flutter client will stay thin: record audio, request microphone permission, upload the
audio file to the backend, and play the returned assistant audio. The backend will own all
sensitive work: audio transcription, prompt construction, API key usage, the chat-completions
request to the local assistant service, and the text-to-speech synthesis step.

The current app already has audio recording, permission handling, Dio, and a voice feature
shell. The current backend already has ASR transcription, a working OpenAI-compatible
chat completions endpoint, and a TTS pipeline. This plan connects those pieces without
pushing LLM logic or speech synthesis into Flutter.

## Key Findings

- The Flutter voice flow was transcript-centric in `app/lib/features/voice/*`.
- `VoiceCaptureCubit` now needs to move from assistant text output to assistant audio output.
- The app already has network plumbing and a shared `Dio` setup, so the client can stay
  simple.
- The backend already exposes `POST /transcribe`, `POST /tts`, and the assistant route is the
  right place to keep prompt keys and model access.
- The backend assistant route should own the full voice round trip and return audio bytes to
  Flutter.

## Scope

In scope:

- Record audio in Flutter and upload it to backend.
- Transcribe audio server-side.
- Call the assistant chat completions API server-side.
- Synthesize assistant reply speech server-side with the existing TTS implementation.
- Return assistant audio to Flutter.
- Update UI state so the screen plays the assistant response, not transcript output.
- Keep sensitive config and prompts in backend env/config only.
- Add tests and docs for the new flow.

Out of scope:

- Full multi-turn memory store.
- Streaming tokens to the UI.
- Client-side prompt assembly.
- Client-side transcription, LLM logic, or TTS logic.
- Public auth/rate limiting rollout beyond the backend guardrails needed for this feature.

## Locked Decisions

- Endpoint: `POST /v1/voice/assistant`
- Request body: multipart form with `file` and optional `language`
- Response body: `audio/mpeg` bytes from the backend TTS pipeline
- Timeout budget: 45 seconds total for the backend request path
- UI state model: `idle`, `recording`, `uploading`, `processing`, `speaking`, `success`, `failure`
  with visible data fields `selectedLanguage` and `failure`

Why this shape:

- The route name says exactly what it does: voice in, assistant speech out.
- Multipart keeps the audio upload path simple and consistent with the current app.
- Returning raw audio keeps Flutter thin and keeps transcript text, prompt internals, and
  assistant reply text on the backend.
- 45 seconds gives room for upload, transcription, the local chat-completions call, and TTS
  without making the UI feel hung forever.

## Phases

| Phase | Name | Status |
|-------|------|--------|
| 1 | [Contract And Flow Design](./phase-01-contract-and-flow-design.md) | Complete |
| 2 | [Backend Assistant Orchestration](./phase-02-backend-assistant-orchestration.md) | Complete |
| 3 | [Flutter Client Refactor](./phase-03-flutter-client-refactor.md) | Complete |
| 4 | [Tests And Validation](./phase-04-tests-and-validation.md) | Complete |
| 5 | [Docs And Guardrails](./phase-05-docs-and-guardrails.md) | Complete |
| 6 | [Speech Output Integration](./phase-06-speech-output-integration.md) | Complete |

## Dependencies

- Backend must keep the existing transcription route stable until the assistant path is live.
- Backend must own the assistant API key, base URL, and system prompt.
- Flutter must only know the backend base URL, never the assistant provider URL.
- Flutter must have an audio player dependency before it can consume the new backend response.

## Success Criteria

- Speaking into the app produces assistant speech instead of transcript text.
- The Flutter client never calls the assistant provider directly.
- Sensitive prompt text and provider credentials never leave the backend.
- The client contract stays limited to raw audio plus minimal routing metadata.
- The old transcript-only UI state is replaced with an assistant-oriented speech state model.
- Backend and Flutter tests pass.
- Runtime docs explain the new flow and its security implications.

## Risks

- Combined transcription + LLM + TTS latency may exceed the current request timeout.
- The new backend endpoint can become an abuse target if left public without limits.
- The app can drift if the client and backend response shape are not locked down early.
- Audio playback compatibility can break if the client does not handle the response bytes
  correctly across platforms.
- Accidentally exposing transcript text in the client defeats the privacy requirement.

## Next Steps

1. Wire the backend assistant route to synthesize speech before returning.
2. Refactor Flutter to request and play audio bytes.
3. Write tests around the full request chain.
4. Update docs and operational notes.
