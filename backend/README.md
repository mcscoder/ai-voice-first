# Backend

Minimal FastAPI backend for the AI Voice First app.

## Run

```bash
cd backend
uv run python main.py
```

Open `http://127.0.0.1:8000/docs` for the generated API docs.

Set a JWT signing secret before using auth-protected routes:

```bash
export AUTH_SECRET_KEY=replace_with_at_least_32_random_bytes
```

Create a user with `POST /auth/register`, then pass the returned access token
as `Authorization: Bearer <token>` on ASR, TTS, voice assistant, and telemetry
requests.

## Dashboard

Run the live Streamlit dashboard in a second terminal:

```bash
cd backend
uv run streamlit run dashboard.py
```

The dashboard uses `GET /v1/voice/assistant/telemetry/stream` with
Server-Sent Events and visualizes the current assistant pipeline: request
intake, ASR, memory retrieval, DeepSeek streaming, VieNeu TTS chunks, client
stream completion, and Mem0 background persistence.

By default, the telemetry stream is authenticated. Paste a user access token
into the dashboard sidebar to track that user's runs. For local development
only, you can make telemetry public and track all runs:

```bash
export TELEMETRY_PUBLIC_STREAM=enabled
```

Do not enable public telemetry on an internet-exposed backend; transcripts and
memory snippets can appear in pipeline metadata.

## Development Principles

- Fail fast: let unexpected errors surface instead of hiding them behind
  defensive fallbacks.
- Do not wrap backend code in broad `try`/`except` blocks. Catch only errors
  with a clear recovery path or when translating a known failure into an API
  response.

## ASR

```bash
curl -F "file=@speech.wav" -F "language=English" http://127.0.0.1:8000/asr
```

The ASR endpoint uses `Qwen/Qwen3-ASR-0.6B`, loads the model on app startup
with 8-bit bitsandbytes quantization, and supports English (`en`) and
Vietnamese (`vi`).

Change `app.core.config.AsrConfig.quantization_level` to adjust ASR
quantization. Supported values are `none`, `int8`, `int4-nf4`, and `int4-fp4`.

## Memory

The memory service uses Mem0 with:

- DeepSeek as the LLM provider
- `Qwen/Qwen3-Embedding-0.6B` through the Hugging Face embedder with 8-bit
  bitsandbytes quantization
- Local Qdrant storage under `backend/app/data/mem0`

Change `app.core.config.MemoryConfig.embedding_quantization_level` to adjust
embedding model quantization independently. Supported values are `none`,
`int8`, `int4-nf4`, and `int4-fp4`.

Set `DEEPSEEK_API_KEY` before starting the backend:

```bash
export DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

`app.core.config.MemoryConfig` defaults to `deepseek-v4-flash` through the
official DeepSeek beta API base URL for strict tool-call schema support.
DeepSeek thinking mode defaults to disabled for lower voice latency. Set
`DEEPSEEK_THINKING=enabled` to opt back into thinking mode.

## Runtime Notes

Current local test hardware uses an NVIDIA RTX 2080S with 8GB VRAM.

Observed voice assistant run:

```text
HTTP Request: POST https://api.deepseek.com/beta/chat/completions "HTTP/1.1 200 OK"
Total existing memories: 0
voice_assistant step=memory duration_ms=4726.48
voice_assistant step=tts duration_ms=8291.70
voice_assistant step=total duration_ms=14224.81
```

Run the real memory integration test with:

```bash
cd backend
uv run pytest tests/test_memory_service_integration.py -q
```

## TTS

```bash
curl -X POST http://127.0.0.1:8000/tts \
  -H "Content-Type: application/json" \
  -d '{"text":"Xin chào, tôi là VieNeu TTS.","voice":"Bình"}' \
  --output speech.wav
```

### Reference Voices

| File | Gender | Accent | Description |
| --- | --- | --- | --- |
| Bình | Male | North | Male voice, North accent |
| Tuyên | Male | North | Male voice, North accent |
| Nguyên | Male | South | Male voice, South accent |
| Hương | Female | North | Female voice, North accent |
| Ngọc | Female | North | Female voice, North accent |
| Đoan | Female | South | Female voice, South accent |
