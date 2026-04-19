# Parakeet Vietnamese Backend

FastAPI backend for `nvidia/parakeet-ctc-0.6b-Vietnamese`, implemented with NVIDIA NeMo.

## Docs

- GPU setup guide: [docs/GPU_SETUP.md](docs/GPU_SETUP.md)

## Runtime

- Linux is the supported deployment OS.
- NVIDIA GPU is the intended runtime target.
- NeMo’s current speech installation guidance requires Python `3.12+` and PyTorch `2.7+`.
- First model download may require accepting NVIDIA’s license on Hugging Face for `nvidia/parakeet-ctc-0.6b-Vietnamese`.

## Run

1. Create a Python `3.12` environment.
2. Install project dependencies:

```bash
uv sync
```

3. Start the API:

```bash
uv run python main.py
```

The app reads configuration from `.env` automatically.

## Configuration

Common settings in `.env`:

```env
HOST=0.0.0.0
PORT=8000
PARAKEET_DEVICE=cuda
PARAKEET_LOAD_ON_STARTUP=true
```

## API

- `POST /transcribe`
- Request: `multipart/form-data` with `file`
- Response: `text`, `model`, `filename`, `content_type`

The backend is intentionally single-model and Vietnamese-focused. Whisper-specific language selection and metadata are removed.
