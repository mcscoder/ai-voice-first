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
WHISPER_MODEL=base
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8
WHISPER_LOAD_ON_STARTUP=true
```

- `WHISPER_DEVICE=cpu` is the safe default.
- `WHISPER_DEVICE=cuda` requires the supported NVIDIA runtime described in `docs/GPU_SETUP.md`.

## Transcription API

`POST /transcribe` accepts a multipart audio file and optional form `language`.

```bash
curl -X POST http://localhost:8000/transcribe \
  -F "file=@sample.wav" \
  -F "language=auto"
```

The backend uses local Faster Whisper for transcription.

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
