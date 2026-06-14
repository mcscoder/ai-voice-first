# Backend

Minimal FastAPI backend for the AI Voice First app.

## Run

```bash
cd backend
uv run python main.py
```

Open `http://127.0.0.1:8000/docs` for the generated API docs.

## ASR

```bash
curl -F "file=@speech.wav" -F "language=English" http://127.0.0.1:8000/asr
```

The ASR endpoint uses `Qwen/Qwen3-ASR-0.6B`, loads the model on app startup,
and supports English (`en`) and Vietnamese (`vi`).

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
