# GPU Setup Guide

This project uses Gipformer (`g-group-ai-lab/gipformer-65M-rnnt`) through `sherpa-onnx`.

This guide covers the official NVIDIA Linux installation path for enabling GPU execution on Ubuntu and Debian.

## Requirements

Before enabling GPU mode, the target system must provide:

- a compatible NVIDIA GPU
- a compatible NVIDIA driver
- CUDA 12.x
- cuDNN for CUDA 12.x

For this backend, install the CUDA 12 package line explicitly. Do not replace it with the unversioned `cuda-toolkit` meta-package.

At the time of writing, the backend ASR stack can run on CPU by default. If you need GPU acceleration, install CUDA 12.x and cuDNN 12.x, then use a GPU-capable ONNX Runtime stack on the host.

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

### 3. Install cuDNN for CUDA 12.x

```bash
sudo apt-get update
sudo apt-get -y install cudnn9-cuda-12
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

### 4. Install cuDNN for CUDA 12.x

```bash
sudo apt-get update
sudo apt-get -y install cudnn9-cuda-12
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
ASR_DECODING_METHOD=modified_beam_search
```

Install project dependencies and start the application:

```bash
uv sync
uv run python main.py
```

## Backend Requirements

The backend ASR stack uses Sherpa ONNX + Hugging Face model files. Validate GPU runtime compatibility (CUDA/cuDNN/ONNX Runtime) on your exact deployment image before rolling to production.

## Source Links

- Gipformer model card: https://huggingface.co/g-group-ai-lab/gipformer-65M-rnnt
- Gipformer repository: https://github.com/ggroup-ai-lab/gipformer
- Sherpa ONNX: https://github.com/k2-fsa/sherpa-onnx
- NVIDIA CUDA installation guide for Linux: https://docs.nvidia.com/cuda/archive/12.6.3/cuda-installation-guide-linux/index.html
- NVIDIA cuDNN installation guide for Linux: https://docs.nvidia.com/deeplearning/cudnn/installation/latest/linux.html
