# GPU Setup Guide

This backend is designed for `nvidia/parakeet-ctc-0.6b-Vietnamese` running through NVIDIA NeMo on Linux.

## Target Runtime

- Linux
- Python `3.12+`
- NVIDIA GPU
- PyTorch `2.7+`
- CUDA-compatible driver/runtime matching the selected PyTorch wheel

NeMo’s current speech installation guidance recommends installing PyTorch before NeMo so the CUDA wheel matches the host GPU runtime.

## Project Dependency Strategy

The project manifest pins:

- `nemo_toolkit[asr]` for the ASR runtime
- `torch==2.7.1`
- the Linux torch index at `https://download.pytorch.org/whl/cu128`

If your deployment needs a different CUDA build, update the torch pin and UV index together before running `uv lock`.

## Setup Flow

1. Install a supported NVIDIA driver on the host.
2. Create a Python `3.12` environment.
3. Sync dependencies:

```bash
uv sync
```

4. Configure the backend:

```env
PARAKEET_DEVICE=cuda
PARAKEET_LOAD_ON_STARTUP=true
```

5. Start the API:

```bash
uv run python main.py
```

## Model Notes

- The backend loads the public model id `nvidia/parakeet-ctc-0.6b-Vietnamese`.
- If NeMo resolves the checkpoint through the shorter alias `nvidia/parakeet-ctc-0.6b-vi`, the backend handles that internally.
- Supported input formats from the model card are `.wav`, `.mp3`, `.flac`, `.ogg`, and `.m4a`.
- The model card states mono audio is required.

## Source Links

- NeMo speech installation: https://docs.nvidia.com/nemo/speech/nightly/starthere/install.html
- NeMo ASR overview: https://docs.nvidia.com/nemo-framework/user-guide/latest/nemotoolkit/asr/intro.html
- Parakeet Vietnamese model card: https://huggingface.co/nvidia/parakeet-ctc-0.6b-Vietnamese
- PyTorch previous versions: https://pytorch.org/get-started/previous-versions/
