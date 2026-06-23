# APPENDIX A. INSTALLATION AND SYSTEM CONFIGURATION GUIDE

## 1. Hardware requirements and test environment

### 1.1. Server-side configuration (Backend)
To avoid latency in speech recognition and synthesis, the service server requires the following recommended configuration:
*   **Operating system:** Linux Ubuntu 20.04 LTS or later.
*   **CPU:** Intel Xeon or AMD Ryzen 8 cores (recommended).
*   **RAM:** 16 GB or more.
*   **GPU:** NVIDIA GPU with CUDA support; the current test environment uses an RTX 2080S with 8GB VRAM.
*   **Environment:** Python >= 3.12, with dependencies managed by `uv`.

### 1.2. Client-side configuration (Frontend)
*   **Mobile OS:** Android 9.0 (API Level 28) or later, or iOS 15.0 or later.
*   **Development environment:** Flutter SDK >= 3.8.0, Dart SDK >= 3.0.

---

## 2. Detailed backend installation guide

### Step 2.1: Clone the source and enter the directory
Open a terminal and move into the backend project directory:
```bash
git clone <repository_url>
cd ai-voice-first/backend
```

### Step 2.2: Install `uv` and create a virtual environment
Use `uv` to initialize the environment and install dependencies quickly:
```bash
# Install uv globally (if needed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create a Python virtual environment
uv venv

# Activate the virtual environment
source .venv/bin/activate
```

### Step 2.3: Sync dependencies
The system reads `pyproject.toml` to automatically install packages including `fastapi`, `uvicorn`, `qwen-asr`, `vieneu`, and `mem0ai`:
```bash
uv sync
```

### Step 2.4: Configure environment variables (`backend/.env`)
Create a `.env` file in the `backend/` directory to configure API keys and memory settings:
```env
# Application environment (development/production)
APP_ENV=development

# API key for the LLM used by Mem0
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# Server port configuration
PORT=8000
HOST=0.0.0.0
```

### Step 2.5: Start the backend server
Run `main.py` to start the FastAPI server:
```bash
python main.py
```
The server will listen on `http://localhost:8000`. You can open `http://localhost:8000/docs` to view the API documentation in Swagger UI.

---

## 3. Detailed frontend installation guide (Flutter App)

### Step 3.1: Move into the app directory and install dependencies
```bash
cd ../app
flutter pub get
```

### Step 3.2: Configure mobile environment variables (`app/.env`)
Create a `.env` file at the root of the Flutter client to route connections to the backend server:
```env
# URL of the running FastAPI backend server
BACKEND_URL=http://<IP_MAY_CHU_BACKEND>:8000
```
*Note:* If running on an emulator/simulator, you can use `http://10.0.2.2:8000` for Android emulators or `http://localhost:8000` for iOS simulators.

### Step 3.3: Run the code on a mobile device
Connect a mobile device or launch an emulator, then run:
```bash
flutter run
```
The system will compile the source code and install the VocalMind app directly on the device.
