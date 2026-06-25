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
official DeepSeek API base URL.

## Runtime Notes

Current local test hardware uses an NVIDIA RTX 2080S with 8GB VRAM.

Observed voice assistant run:

```text
HTTP Request: POST https://api.deepseek.com/chat/completions "HTTP/1.1 200 OK"
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
