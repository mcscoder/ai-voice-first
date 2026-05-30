from __future__ import annotations

import asyncio
import os
import time
import uuid
from enum import StrEnum
from multiprocessing import Process, Queue
from threading import Thread
from typing import Any

from dotenv import load_dotenv


load_dotenv()

REPO_ID = "g-group-ai-lab/gipformer-65M-rnnt"
SAMPLE_RATE = 16000
FEATURE_DIM = 80
ASR_REQUEST_TIMEOUT_SECONDS = 60
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
        import soundfile as sf

        model = self.load_model()
        samples, sample_rate = sf.read(file_path, dtype="float32")
        if samples.ndim > 1:
            samples = samples.mean(axis=1)

        stream = model.create_stream()
        stream.accept_waveform(sample_rate, samples)
        model.decode_streams([stream])
        text = stream.result.text.strip()
        duration_seconds = float(sf.info(file_path).duration)

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
        self.asr_in = Queue()
        self.asr_out = Queue()
        self.waiters: dict[str, tuple[asyncio.AbstractEventLoop, asyncio.Future]] = {}
        self.asr_process: Process | None = None
        self.result_thread: Thread | None = None

    def load_model(self) -> None:
        if self.asr_process is not None and self.asr_process.is_alive():
            return

        self.asr_process = Process(
            target=_run_asr_worker,
            args=(self.asr_in, self.asr_out),
            name="gipformer-asr",
        )
        self.asr_process.start()
        while self.asr_out.empty():
            if not self.asr_process.is_alive():
                raise RuntimeError("ASR worker exited while loading.")
            time.sleep(0.1)
        self.asr_out.get()
        self.result_thread = Thread(target=self._asr_result_loop, daemon=True)
        self.result_thread.start()

    def shutdown_model(self) -> None:
        if self.asr_process is None:
            return

        if self.asr_process.is_alive():
            self.asr_in.put({"cmd": "STOP"})
            self.asr_process.join(timeout=5)

        if self.asr_process.is_alive():
            self.asr_process.terminate()
            self.asr_process.join(timeout=5)

        self.asr_process = None

    async def transcribe(
        self,
        file_path: str,
        language: LanguageOption = LanguageOption.AUTO,
    ) -> dict[str, object]:
        self.load_model()

        job_id = str(uuid.uuid4())
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        future.add_done_callback(lambda _: self.waiters.pop(job_id, None))
        self.waiters[job_id] = (loop, future)

        self.asr_in.put({
            "cmd": "RUN",
            "job_id": job_id,
            "file_path": file_path,
            "language": language.value,
        })

        message = await asyncio.wait_for(future, ASR_REQUEST_TIMEOUT_SECONDS)
        return message["result"]

    def _asr_result_loop(self) -> None:
        while True:
            result = self.asr_out.get()
            job_id = result["job_id"]
            waiter = self.waiters.get(job_id)
            if waiter:
                loop, future = waiter
                loop.call_soon_threadsafe(_set_result_if_pending, future, result)


def _run_asr_worker(asr_in: Any, asr_out: Any) -> None:
    asr = _LocalTranscriptionModel()
    asr.load_model()
    asr_out.put({"ready": True})

    while True:
        job = asr_in.get()

        if job["cmd"] == "STOP":
            break

        result = asr.transcribe(
            job["file_path"],
            LanguageOption(job["language"]),
        )
        asr_out.put({
            "job_id": job["job_id"],
            "result": result,
        })


def _set_result_if_pending(future: asyncio.Future, value: dict[str, Any]) -> None:
    if not future.done():
        future.set_result(value)


transcription_service = TranscriptionService()
