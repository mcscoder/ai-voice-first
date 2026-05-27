# Voice to Text Backend

## Docs

- GPU setup guide: [docs/GPU_SETUP.md](docs/GPU_SETUP.md)

## Run

```bash
uv sync
uv run python main.py
```

The app reads configuration from `.env` automatically.

API docs are available at `http://localhost:8000/docs` after startup.

## Configuration

Common settings in `.env`:

```env
HOST=0.0.0.0
PORT=8000
ASR_PRECISION=fp32
ASR_NUM_THREADS=4
ASR_LOAD_ON_STARTUP=true
```

Assistant settings:

```env
ASSISTANT_API_BASE_URL=http://127.0.0.1:8317/v1
ASSISTANT_API_KEY=replace-me
ASSISTANT_MODEL=gemini-2.5-flash-lite
ASSISTANT_PROVIDER_TIMEOUT_SECONDS=30
ASSISTANT_SYSTEM_PROMPT=You are a helpful voice assistant. Reply in {language_name}. Keep answers concise, natural, and useful. Do not mention transcripts or internal processing.
ASSISTANT_STORE_MEMORIES=true
ASSISTANT_USE_MEMORY_CONTEXT=true
```

- `ASR_PRECISION=int8` reduces memory usage and can improve latency.
- `ASR_LOAD_ON_STARTUP=true` preloads ASR model files during app startup.
- ASR model repo and decoding method are hardcoded in backend code to avoid config drift.
- The assistant and memory extractor share the same OpenAI-compatible LLM server.

## Transcription API

`POST /transcribe` accepts a multipart audio file and optional form `language`.

```bash
curl -X POST http://localhost:8000/transcribe \
  -F "file=@sample.wav" \
  -F "language=auto"
```

The backend uses local Gipformer (`g-group-ai-lab/gipformer-65M-rnnt`) via ONNX for transcription.

## Voice Assistant API

`POST /v1/voice/assistant` accepts a multipart audio file and optional form `language`.
The backend transcribes the audio, builds the assistant prompt, calls the local chat
completions service, then synthesizes the reply with the backend TTS pipeline.

```bash
curl -X POST http://localhost:8000/v1/voice/assistant \
  -F "file=@sample.wav" \
  -F "language=vi" \
  --output assistant-speech.mp3
```

The response is `audio/mpeg` bytes.

Validation rules:

- `file` must contain audio bytes.
- `language` is optional and accepts `vi` or `en`.
- Empty uploads are rejected with `400`.
- Empty transcripts are rejected with `400`.
- Assistant replies longer than the TTS limit are rejected with `502`.
- Assistant timeouts return `504`.
- Assistant provider failures return `502`.
- TTS failures return `502`.

The backend owns the assistant API key, base URL, system prompt, and TTS wiring. Flutter
should only upload audio and play the returned speech.

## Text To Speech API

`POST /tts` accepts JSON text and returns MP3 bytes as `audio/mpeg` with
`Content-Disposition: attachment; filename="speech.mp3"`.

Vietnamese is the default language. The backend tries `vi-VN-HoaiMyNeural`
first and falls back to `vi-VN-NamMinhNeural` if Edge TTS returns no audio:

```bash
curl -X POST http://localhost:8000/tts \
  -H "Content-Type: application/json" \
  -d '{"text":"Xin chao"}' \
  --output speech-vi.mp3
```

English voice:

```bash
curl -X POST http://localhost:8000/tts \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello","language":"en"}' \
  --output speech-en.mp3
```

Validation rules:

- `text` is trimmed before synthesis.
- Empty text is rejected.
- Text longer than 5000 characters after trimming is rejected.
- `language` must be `vi` or `en`; omitted language defaults to `vi`.
- Synthesis times out after 30 seconds.
- Upstream synthesis timeouts return `504`.
- Upstream Edge TTS failures return `502`.

Swagger UI can show the endpoint shape, but `curl --output` is better for
checking MP3 output.

TTS uses remote Edge TTS. Submitted text leaves this server for synthesis, and
the remote service can fail or throttle. Add authentication and rate limiting
before exposing this endpoint publicly.

## Test

```bash
uv run python -m compileall .
uv run pytest
```

Live LLM smoke test:

```bash
RUN_LIVE_LLM_SMOKE=1 uv run pytest tests/test_live_llm_server.py -q
```

This test sends real requests to `ASSISTANT_API_BASE_URL` and requires the
LLM server to be reachable from the machine running the test.

Live voice endpoint test:

```bash
RUN_LIVE_VOICE_ENDPOINT=1 uv run pytest tests/test_live_voice_assistant_endpoint.py -q
```

This test generates a real audio sample, sends it through `/v1/voice/assistant`,
and requires the backend plus the LLM and TTS services to be reachable.
