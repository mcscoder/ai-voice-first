from __future__ import annotations

import os
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile


load_dotenv()

PUBLIC_MODEL_NAME = "nvidia/parakeet-ctc-0.6b-Vietnamese"
MODEL_LOAD_CANDIDATES = (
    PUBLIC_MODEL_NAME,
    "nvidia/parakeet-ctc-0.6b-vi",
)


def env_flag(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class AudioTranscriptionError(Exception):
    pass


class BackendTranscriptionError(Exception):
    pass


def load_asr_model_class() -> Any:
    try:
        import nemo.collections.asr as nemo_asr
    except Exception as exc:
        raise BackendTranscriptionError(
            "Failed to import the NVIDIA NeMo ASR runtime. "
            "Install a supported PyTorch + NeMo stack first: "
            f"{type(exc).__name__}: {exc}"
        ) from exc

    return nemo_asr.models.ASRModel


def extract_transcript_text(transcriptions: Any) -> str:
    if isinstance(transcriptions, tuple) and len(transcriptions) == 1:
        transcriptions = transcriptions[0]

    if not transcriptions:
        return ""

    first_result = transcriptions[0]
    text = getattr(first_result, "text", first_result)
    return str(text).strip()


class ParakeetTranscriptionService:
    def __init__(self) -> None:
        self.model_name = PUBLIC_MODEL_NAME
        self.device = os.getenv("PARAKEET_DEVICE", "cuda")
        self._model: Any | None = None

    def load_model(self) -> Any:
        if self._model is not None:
            return self._model

        asr_model_class = load_asr_model_class()
        load_errors: list[str] = []
        model: Any | None = None

        for candidate in MODEL_LOAD_CANDIDATES:
            try:
                model = asr_model_class.from_pretrained(model_name=candidate)
                break
            except Exception as exc:
                load_errors.append(f"{candidate}: {type(exc).__name__}: {exc}")

        if model is None:
            raise BackendTranscriptionError(
                "Failed to initialize the Parakeet transcription model: "
                + " | ".join(load_errors)
            )

        try:
            if hasattr(model, "to"):
                model = model.to(self.device)
            if hasattr(model, "eval"):
                model.eval()
            if hasattr(model, "freeze"):
                model.freeze()
        except Exception as exc:
            raise BackendTranscriptionError(
                "Failed to prepare the Parakeet transcription model on "
                f"device '{self.device}': {type(exc).__name__}: {exc}"
            ) from exc

        self._model = model
        return self._model

    def transcribe(self, file_path: str) -> dict[str, object]:
        try:
            model = self.load_model()
        except BackendTranscriptionError:
            raise

        try:
            transcriptions = model.transcribe([file_path])
            text = extract_transcript_text(transcriptions)
        except RuntimeError as exc:
            raise BackendTranscriptionError(
                "Transcription backend failed: "
                f"{type(exc).__name__}: {exc}"
            ) from exc
        except Exception as exc:
            raise AudioTranscriptionError(
                "Unable to decode or transcribe the provided audio file: "
                f"{type(exc).__name__}: {exc}"
            ) from exc

        return {
            "text": text,
            "model": self.model_name,
        }


service = ParakeetTranscriptionService()


@asynccontextmanager
async def lifespan(_: FastAPI):
    if env_flag("PARAKEET_LOAD_ON_STARTUP", True):
        service.load_model()
    yield


app = FastAPI(
    title="Parakeet Vietnamese Transcription API",
    version="0.2.0",
    lifespan=lifespan,
)


@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)) -> dict[str, object]:
    suffix = Path(file.filename or "").suffix or ".bin"
    bytes_written = 0
    temp_path: str | None = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_path = temp_file.name

            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                temp_file.write(chunk)
                bytes_written += len(chunk)

        if bytes_written == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        result = service.transcribe(temp_path)
        return {
            **result,
            "filename": file.filename,
            "content_type": file.content_type,
        }
    except AudioTranscriptionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except BackendTranscriptionError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        await file.close()
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


def main() -> None:
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
