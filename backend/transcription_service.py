from __future__ import annotations

import asyncio
import logging
import os
import subprocess
import time
from enum import StrEnum
from multiprocessing import Pipe, Process
from multiprocessing.connection import Connection
from typing import Any

from dotenv import load_dotenv


load_dotenv()

REPO_ID = "g-group-ai-lab/gipformer-65M-rnnt"
SAMPLE_RATE = 16000
FEATURE_DIM = 80
ASR_REQUEST_TIMEOUT_SECONDS = 60
FFMPEG_DECODE_TIMEOUT_SECONDS = 20
MAX_COMPRESSED_AUDIO_BYTES = 25 * 1024 * 1024
ONNX_FILES = {
    "fp32": {
        "encoder": "encoder-epoch-35-avg-6.onnx",
        "decoder": "decoder-epoch-35-avg-6.onnx",
        "joiner": "joiner-epoch-35-avg-6.onnx",
    },
    "int8": {
        "encoder": "encoder-epoch-35-avg-6.int8.onnx",
        "decoder": "decoder-epoch-35-avg-6.int8.onnx",
        "joiner": "joiner-epoch-35-avg-6.int8.onnx",
    },
}
logger = logging.getLogger("uvicorn.error")


class AudioTranscriptionError(Exception):
    pass


class BackendTranscriptionError(Exception):
    pass


class LanguageOption(StrEnum):
    AUTO = "auto"
    EN = "en"
    VI = "vi"


class _LocalTranscriptionModel:
    def __init__(self) -> None:
        self.model_name = REPO_ID
        self.precision = os.getenv("ASR_PRECISION", "fp32").lower()
        self.num_threads = int(os.getenv("ASR_NUM_THREADS", "4"))
        self.provider = os.getenv("ASR_PROVIDER", "cuda").strip().lower()
        self.decoding_method = "modified_beam_search"
        self._model: Any | None = None

    def _download_model_paths(self) -> dict[str, str]:
        from huggingface_hub import hf_hub_download

        precision = "int8" if self.precision == "int8" else "fp32"
        file_map = ONNX_FILES[precision]

        paths: dict[str, str] = {}
        for key, filename in file_map.items():
            paths[key] = hf_hub_download(repo_id=self.model_name, filename=filename)
        paths["tokens"] = hf_hub_download(repo_id=self.model_name, filename="tokens.txt")
        return paths

    def load_model(self) -> Any:
        import sherpa_onnx

        if self._model is None:
            model_paths = self._download_model_paths()
            self._model = sherpa_onnx.OfflineRecognizer.from_transducer(
                encoder=model_paths["encoder"],
                decoder=model_paths["decoder"],
                joiner=model_paths["joiner"],
                tokens=model_paths["tokens"],
                num_threads=self.num_threads,
                sample_rate=SAMPLE_RATE,
                feature_dim=FEATURE_DIM,
                decoding_method=self.decoding_method,
                provider=self.provider,
            )
        return self._model

    def transcribe(
        self,
        file_path: str,
        language: LanguageOption = LanguageOption.AUTO,
    ) -> dict[str, object]:
        model = self.load_model()
        samples, sample_rate, duration_seconds = _read_audio_samples(file_path)

        stream = model.create_stream()
        stream.accept_waveform(sample_rate, samples)
        model.decode_streams([stream])
        text = stream.result.text.strip()

        return {
            "text": text,
            "requested_language": language.value,
            "model": self.model_name,
            "language": "vi",
            "language_probability": None,
            "duration_seconds": duration_seconds,
        }


class TranscriptionService:
    def __init__(self) -> None:
        self.asr_connection: Connection | None = None
        self.request_lock = asyncio.Lock()
        self.asr_process: Process | None = None

    def load_model(self) -> None:
        if self.asr_process is not None and self.asr_process.is_alive():
            return

        self.asr_connection, worker_connection = Pipe()
        self.asr_process = Process(
            target=_run_asr_worker,
            args=(worker_connection,),
            name="gipformer-asr",
        )
        self.asr_process.start()
        worker_connection.close()
        while not self.asr_connection.poll():
            if not self.asr_process.is_alive():
                raise RuntimeError("ASR worker exited while loading.")
            time.sleep(0.1)
        self.asr_connection.recv()

    def shutdown_model(self) -> None:
        if self.asr_process is None:
            return

        if self.asr_process.is_alive():
            if self.asr_connection is not None:
                try:
                    self.asr_connection.send({"cmd": "STOP"})
                except (EOFError, OSError):
                    pass
            self.asr_process.join(timeout=5)

        if self.asr_process.is_alive():
            self.asr_process.terminate()
            self.asr_process.join(timeout=5)

        if self.asr_connection is not None:
            try:
                self.asr_connection.close()
            except OSError:
                pass
            self.asr_connection = None
        self.asr_process = None

    async def transcribe(
        self,
        file_path: str,
        language: LanguageOption = LanguageOption.AUTO,
    ) -> dict[str, object]:
        async with self.request_lock:
            self.load_model()
            if self.asr_connection is None:
                raise RuntimeError("ASR worker is not connected.")

            self.asr_connection.send({
                "cmd": "RUN",
                "file_path": file_path,
                "language": language.value,
            })

            try:
                message = await asyncio.wait_for(
                    asyncio.to_thread(self.asr_connection.recv),
                    ASR_REQUEST_TIMEOUT_SECONDS,
                )
            except TimeoutError as exc:
                self.shutdown_model()
                raise BackendTranscriptionError("ASR worker timed out.") from exc
            except (EOFError, OSError) as exc:
                self.shutdown_model()
                raise BackendTranscriptionError("ASR worker disconnected.") from exc
            return _result_from_worker_message(message)


def _run_asr_worker(connection: Connection) -> None:
    asr = _LocalTranscriptionModel()
    asr.load_model()
    connection.send({"ready": True})

    while True:
        job = connection.recv()

        if job["cmd"] == "STOP":
            break

        try:
            result = asr.transcribe(
                job["file_path"],
                LanguageOption(job["language"]),
            )
            connection.send({
                "result": result,
            })
        except AudioTranscriptionError as exc:
            connection.send({
                "error": {
                    "type": "audio",
                    "message": str(exc),
                },
            })
        except BackendTranscriptionError as exc:
            logger.exception("ASR worker backend transcription error.")
            connection.send({
                "error": {
                    "type": "backend",
                    "message": str(exc),
                },
            })
        except Exception:
            logger.exception("Unexpected ASR worker transcription error.")
            connection.send({
                "error": {
                    "type": "backend",
                    "message": "ASR worker failed to transcribe audio.",
                },
            })

    connection.close()


def _result_from_worker_message(message: dict[str, Any]) -> dict[str, object]:
    if "error" not in message:
        return message["result"]

    error = message["error"]
    if error["type"] == "audio":
        raise AudioTranscriptionError(error["message"])
    raise BackendTranscriptionError(error["message"])


def _read_audio_samples(file_path: str) -> tuple[Any, int, float]:
    import soundfile as sf

    try:
        samples, sample_rate = sf.read(file_path, dtype="float32")
    except sf.LibsndfileError:
        return _read_audio_samples_with_ffmpeg(file_path)

    if samples.ndim > 1:
        samples = samples.mean(axis=1)
    duration_seconds = float(len(samples) / sample_rate) if sample_rate else 0.0
    return samples, int(sample_rate), duration_seconds


def _read_audio_samples_with_ffmpeg(file_path: str) -> tuple[Any, int, float]:
    import numpy as np

    if os.path.getsize(file_path) > MAX_COMPRESSED_AUDIO_BYTES:
        raise AudioTranscriptionError("Uploaded audio is too large to decode.")

    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        file_path,
        "-ac",
        "1",
        "-ar",
        str(SAMPLE_RATE),
        "-f",
        "f32le",
        "-",
    ]
    try:
        completed = subprocess.run(
            command,
            check=True,
            capture_output=True,
            timeout=FFMPEG_DECODE_TIMEOUT_SECONDS,
        )
    except FileNotFoundError as exc:
        raise BackendTranscriptionError(
            "Compressed audio requires ffmpeg to be installed."
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise AudioTranscriptionError("Uploaded audio took too long to decode.") from exc
    except subprocess.CalledProcessError as exc:
        raise AudioTranscriptionError("Uploaded audio could not be decoded.") from exc

    samples = np.frombuffer(completed.stdout, dtype=np.float32)
    if samples.size == 0:
        raise AudioTranscriptionError("Uploaded audio could not be decoded.")

    duration_seconds = float(samples.size / SAMPLE_RATE)
    return samples, SAMPLE_RATE, duration_seconds


transcription_service = TranscriptionService()
