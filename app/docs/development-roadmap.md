# Development Roadmap

## Delivered

- Voice assistant speech flow is shipped: Flutter records audio, uploads it to the backend,
  and plays the assistant response audio.
- Transcript text, prompt assembly, provider credentials, and TTS synthesis stay backend-only.
- The backend route now returns `audio/mpeg` bytes instead of a JSON reply payload.

## Immediate

- Replace placeholder package identifiers when a real organization identifier is available.
- Keep generated files current.

## Short Term

- Add product analytics events tied to real user flows.
- Add public-exposure hardening for backend routes: auth, rate limits, and request limits.

## Ongoing

- Remove unused infrastructure if product scope does not require it.
- Keep docs aligned with the implemented architecture.
