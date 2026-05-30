# GPU Setup Guide

This project uses Gipformer (`g-group-ai-lab/gipformer-65M-rnnt`) through
`sherpa-onnx` for ASR, and VieNeu TTS v2 Turbo
(`pnnbao-ump/VieNeu-TTS-v2-Turbo`) through `vieneu[gpu]` for local speech
synthesis.

This guide covers the official NVIDIA Linux installation path for enabling GPU execution on Ubuntu and Debian.

## Requirements

Before enabling GPU mode, the target system must provide:

- a compatible NVIDIA GPU
- a compatible NVIDIA driver
- CUDA 12.x
- cuDNN for CUDA 12.x
- ONNX Runtime GPU with `CUDAExecutionProvider`
- eSpeak NG for VieNeu text normalization and phonemization

For this backend, install the CUDA 12 package line explicitly. Do not replace it with the unversioned `cuda-toolkit` meta-package.

At the time of writing, the backend ASR stack can run on CPU by default. The TTS
stack is configured for CUDA and should fail during preload if the GPU runtime is
not available.

## Supported Linux Targets

This guide documents the Debian-family package-manager path for:

- Ubuntu 22.04
- Ubuntu 24.04
- Debian 12

## Ubuntu Setup

### 1. Add the NVIDIA CUDA repository

Ubuntu 22.04:

```bash
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt-get update
```

Ubuntu 24.04:

```bash
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2404/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt-get update
```

### 2. Install the NVIDIA driver and CUDA 12.x toolkit

```bash
sudo apt-get install -y cuda-drivers
sudo apt-get install -y cuda-toolkit-12
```

### 3. Install cuDNN and eSpeak NG

```bash
sudo apt-get update
sudo apt-get -y install cudnn9-cuda-12
sudo apt-get -y install espeak-ng
```

### 4. Complete the platform installation

```bash
sudo reboot
```

After the system restarts, continue with the project configuration section below.

## Debian 12 Setup

### 1. Prepare the package sources

```bash
sudo add-apt-repository contrib
sudo apt-key del 7fa2af80
```

### 2. Add the NVIDIA CUDA repository

```bash
wget https://developer.download.nvidia.com/compute/cuda/repos/debian12/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt-get update
```

### 3. Install the NVIDIA driver and CUDA 12.x toolkit

```bash
sudo apt-get install -y cuda-drivers
sudo apt-get install -y cuda-toolkit-12
```

### 4. Install cuDNN and eSpeak NG

```bash
sudo apt-get update
sudo apt-get -y install cudnn9-cuda-12
sudo apt-get -y install espeak-ng
```

### 5. Complete the platform installation

```bash
sudo reboot
```

After the system restarts, continue with the project configuration section below.

## Project Configuration

Set ASR mode in the project environment:

```env
ASR_MODEL=g-group-ai-lab/gipformer-65M-rnnt
ASR_PRECISION=int8
ASR_NUM_THREADS=4
ASR_PROVIDER=cuda
ASR_DECODING_METHOD=modified_beam_search
TTS_LOAD_ON_STARTUP=true
```

Install project dependencies and start the application:

```bash
uv sync
uv run python main.py
```

The project keeps Sherpa's CUDA wheel page in `pyproject.toml` as a uv
`find-links` source. That lets `uv sync`, `uv lock`, and future dependency
changes resolve `sherpa-onnx==1.13.2+cuda12.cudnn9` without repeating the
manual `-f https://k2-fsa.github.io/sherpa/onnx/cuda.html` flag.

## Backend Requirements

The backend ASR stack uses Sherpa ONNX + Hugging Face model files in an internal
worker process. The backend TTS stack uses VieNeu + Torch/CUDA + ONNX Runtime
GPU in another internal worker process. FastAPI talks to both workers through
local process queues, not HTTP. Startup preload downloads and warms model files
when `ASR_LOAD_ON_STARTUP=true` and `TTS_LOAD_ON_STARTUP=true`, so missing CUDA
provider support, eSpeak NG, model cache access, and MP3 encoding support fail
before the API serves traffic.
Validate this exact deployment image before rolling to production.

## Source Links

- Gipformer model card: https://huggingface.co/g-group-ai-lab/gipformer-65M-rnnt
- Gipformer repository: https://github.com/ggroup-ai-lab/gipformer
- Sherpa ONNX: https://github.com/k2-fsa/sherpa-onnx
- VieNeu TTS v2 Turbo model card: https://huggingface.co/pnnbao-ump/VieNeu-TTS-v2-Turbo
- VieNeu SDK docs: https://docs.vieneu.io/docs/sdk/overview/
- NVIDIA CUDA installation guide for Linux: https://docs.nvidia.com/cuda/archive/12.6.3/cuda-installation-guide-linux/index.html
- NVIDIA cuDNN installation guide for Linux: https://docs.nvidia.com/deeplearning/cudnn/installation/latest/linux.html
