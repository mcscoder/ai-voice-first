# GPU Setup Guide

This project uses `faster-whisper` on top of `ctranslate2` for transcription.

This guide covers the official NVIDIA Linux installation path for enabling GPU execution on Ubuntu and Debian.

## Requirements

Before enabling GPU mode, the target system must provide:

- a compatible NVIDIA GPU
- a compatible NVIDIA driver
- CUDA 12.x
- cuDNN for CUDA 12.x

For this backend, install the CUDA 12 package line explicitly. Do not replace it with the unversioned `cuda-toolkit` meta-package.

At the time of writing, the upstream backend documentation states that CTranslate2 Python wheels support GPU execution on Linux and Windows and require CUDA 12.x. For speech recognition workloads, the current faster-whisper and CTranslate2 documentation also require cuDNN with the CUDA 12 stack.

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

Set GPU mode in the project environment:

```env
WHISPER_DEVICE=cuda
```

Install project dependencies and start the application:

```bash
uv sync
uv run python main.py
```

## Backend Requirements

The current upstream documentation says:

- CTranslate2 Python wheels support GPU execution on Linux and Windows, and require CUDA 12.x.
- For speech recognition models with convolutional layers, CTranslate2 documentation calls for cuDNN with the CUDA 12.x stack.
- The faster-whisper README for recent versions says GPU execution requires `cuBLAS` for CUDA 12 and `cuDNN` for CUDA 12.

Because this project uses `faster-whisper`, verify backend compatibility against the current faster-whisper README before changing CUDA, cuDNN, or backend package versions.

## Source Links

- CTranslate2 installation docs: https://opennmt.net/CTranslate2/installation.html
- CTranslate2 hardware support: https://opennmt.net/CTranslate2/hardware_support.html
- faster-whisper README: https://github.com/SYSTRAN/faster-whisper
- NVIDIA CUDA installation guide for Linux: https://docs.nvidia.com/cuda/archive/12.6.3/cuda-installation-guide-linux/index.html
- NVIDIA cuDNN installation guide for Linux: https://docs.nvidia.com/deeplearning/cudnn/installation/latest/linux.html
