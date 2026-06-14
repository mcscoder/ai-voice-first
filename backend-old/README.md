# Voice to Text Backend

## Docs

- GPU setup guide: [docs/GPU_SETUP.md](docs/GPU_SETUP.md)

## Run

```bash
uv sync
uv run python main.py
```

API docs are available at `http://localhost:8000/docs` after startup.

## Configuration

Configuration is hardcoded in `config.py`.

- ASR precision, thread count, CUDA provider, and startup preload are set in `config.py`.
- TTS startup preload is set in `config.py`.
- `ffmpeg` must be installed on the host so Android `.m4a`/AAC uploads can be
  decoded before ASR.
- ASR model repo and decoding method are hardcoded in backend code to avoid config drift.
- TTS model repo and GPU mode are hardcoded in backend code to avoid config drift.
- `mem0ai==1.0.11` now handles long-term memory and keeps its local store under
  `backend/.data/mem0/`.
- The mem0 LLM uses `gemini-2.5-flash-lite`.
- The mem0 embedder uses `Qwen/Qwen3-Embedding-0.6B`.
- The backend appends a speech-output instruction to assistant prompts because
  replies are spoken directly by TTS and Markdown artifacts sound unnatural.
- Memory context retrieval and transcript storage use mem0.

## Transcription API

`POST /transcribe` accepts a multipart audio file.

```bash
curl -X POST http://localhost:8000/transcribe \
  -F "file=@sample.wav"
```

The backend uses local Gipformer (`g-group-ai-lab/gipformer-65M-rnnt`) via ONNX for transcription.

## Voice Assistant API

`POST /v1/voice/assistant` accepts a multipart audio file.
The backend transcribes the audio, uses mem0 for memory retrieval, reply generation,
and memory storage, then synthesizes the reply with the backend TTS pipeline.

```bash
curl -X POST http://localhost:8000/v1/voice/assistant \
  -F "file=@sample.wav" \
  --output assistant-speech.mp3
```

The response is `audio/mpeg` bytes.

Validation rules:

- `file` must contain audio bytes.
- Empty uploads are rejected with `400`.
- Empty transcripts are rejected with `400`.
- Unreadable, oversized, or slow compressed audio returns `400`.
- Missing `ffmpeg` for Android `.m4a`/AAC uploads is a backend setup error and
  returns `500`.
- Assistant replies longer than the TTS limit are rejected with `502`.
- Assistant timeouts return `504`.
- Assistant provider failures return `502`.
- TTS empty-audio and synthesis failures return `502`.

The backend owns mem0 configuration, prompt construction, and TTS wiring. Flutter
should only upload audio and play the returned speech.

## Text To Speech API

`POST /tts` accepts JSON text and returns MP3 bytes as `audio/mpeg` with
`Content-Disposition: attachment; filename="speech.mp3"`.

The backend synthesizes Vietnamese speech locally with
VieNeu TTS v2 Turbo (`pnnbao-ump/VieNeu-TTS-v2-Turbo`) on CUDA, then encodes
the 24 kHz waveform to MP3:

```bash
curl -X POST http://localhost:8000/tts \
  -H "Content-Type: application/json" \
  -d '{"text":"Xin chao"}' \
  --output speech-vi.mp3
```

Validation rules:

- `text` is trimmed before synthesis.
- Empty text is rejected.
- Text longer than 5000 characters after trimming is rejected.
- Missing TTS audio returns `502`; runtime failures are not wrapped.

Swagger UI can show the endpoint shape, but `curl --output` is better for
checking MP3 output.

ASR and TTS run in separate internal worker processes. Startup can download and
warm the Hugging Face model caches, and the host must provide a CUDA-capable
NVIDIA runtime, GPU ONNX Runtime, and eSpeak NG. FastAPI talks to workers
through local process pipes, not HTTP. Keep this service on a trusted network
unless authentication and rate limiting are added because speech synthesis
consumes GPU resources.
