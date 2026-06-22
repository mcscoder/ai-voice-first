# Backend

Minimal FastAPI backend for the AI Voice First app.

## Run

```bash
cd backend
uv run python main.py
```

Open `http://127.0.0.1:8000/docs` for the generated API docs.

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
with 4-bit bitsandbytes quantization, and supports English (`en`) and
Vietnamese (`vi`).

## Memory

The memory service uses Mem0 with:

- Gemini as the LLM provider
- `Qwen/Qwen3-Embedding-0.6B` through the Hugging Face embedder with 4-bit
  bitsandbytes quantization
- Local Qdrant storage under `backend/app/data/mem0`

The Gemini API key in `app.core.config.MemoryConfig` is a mock placeholder. For
local development, Gemini calls are routed through the local proxy server by
patching Mem0's installed Gemini adapter:

```python
self.client = genai.Client(
    api_key=api_key,
    http_options={"base_url": "http://127.0.0.1:8317"},
)
```

Patch location:

```text
.venv/lib/python3.12/site-packages/mem0/llms/gemini.py
```

This is a local virtualenv patch and is not tracked by git. Reinstalling or
syncing dependencies can overwrite it.

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
