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
