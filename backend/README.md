# Voice to Text Backend

## Docs

- GPU setup guide: [docs/GPU_SETUP.md](docs/GPU_SETUP.md)

## Run

```bash
uv sync
uv run python main.py
```

The app reads configuration from `.env` automatically.

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
