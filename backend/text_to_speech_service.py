from __future__ import annotations

import asyncio
import io
import time
import uuid
from multiprocessing import Process, Queue
from threading import Thread
from typing import Any

import soundfile as sf


MAX_TEXT_LENGTH = 5000
TTS_REQUEST_TIMEOUT_SECONDS = 60
VIE_NEU_SAMPLE_RATE = 24_000
VIE_NEU_MODE = "turbo_gpu"
VIE_NEU_BACKBONE_REPO = "pnnbao-ump/VieNeu-TTS-v2-Turbo"
VIE_NEU_CODEC_REPO = "pnnbao-ump/VieNeu-Codec"
VIE_NEU_DEVICE = "cuda"
VIE_NEU_BACKEND = "standard"
TTS_WARMUP_TEXT = "Xin chào, đây là kiểm tra khởi động."


class TextToSpeechNoAudioError(Exception):
    pass


class TextToSpeechService:
    def __init__(self) -> None:
        self.tts_in = Queue()
        self.tts_out = Queue()
        self.waiters: dict[str, tuple[asyncio.AbstractEventLoop, asyncio.Future]] = {}
        self.tts_process: Process | None = None
        self.result_thread: Thread | None = None

    def load_model(self) -> None:
        if self.tts_process is not None and self.tts_process.is_alive():
            return

        self.tts_process = Process(
            target=_run_tts_worker,
            args=(self.tts_in, self.tts_out),
            name="vieneu-tts",
        )
        self.tts_process.start()
        while self.tts_out.empty():
            if not self.tts_process.is_alive():
                raise RuntimeError("VieNeu TTS worker exited while loading.")
            time.sleep(0.1)
        self.tts_out.get()
        self.result_thread = Thread(target=self._result_loop, daemon=True)
        self.result_thread.start()

    async def synthesize(self, text: str) -> bytes:
        self.load_model()

        job_id = str(uuid.uuid4())
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        future.add_done_callback(lambda _: self.waiters.pop(job_id, None))
        self.waiters[job_id] = (loop, future)

        self.tts_in.put({
            "cmd": "RUN",
            "job_id": job_id,
            "text": text,
        })

        result = await asyncio.wait_for(future, TTS_REQUEST_TIMEOUT_SECONDS)
        return result["audio"]

    def _result_loop(self) -> None:
        while True:
            result = self.tts_out.get()
            job_id = result["job_id"]
            waiter = self.waiters.get(job_id)
            if waiter:
                loop, future = waiter
                loop.call_soon_threadsafe(_set_result_if_pending, future, result)

    def shutdown_model(self) -> None:
        if self.tts_process is None:
            return

        if self.tts_process.is_alive():
            self.tts_in.put({"cmd": "STOP"})
            self.tts_process.join(timeout=5)

        if self.tts_process.is_alive():
            self.tts_process.terminate()
            self.tts_process.join(timeout=5)

        self.tts_process = None


def load_tts_model() -> None:
    tts_service.load_model()


def shutdown_tts_model() -> None:
    tts_service.shutdown_model()


async def synthesize_speech(text: str, language: str) -> bytes:
    del language
    return await tts_service.synthesize(text)


def _run_tts_worker(tts_in: Any, tts_out: Any) -> None:
    tts = _create_tts_engine()
    _synthesize_with_engine(tts, TTS_WARMUP_TEXT)
    tts_out.put({"ready": True})

    while True:
        job = tts_in.get()

        if job["cmd"] == "STOP":
            break

        audio = _synthesize_with_engine(tts, job["text"])
        tts_out.put({
            "job_id": job["job_id"],
            "audio": audio,
        })


def _create_tts_engine() -> Any:
    from vieneu import Vieneu

    _ensure_cuda_provider_available()
    return Vieneu(
        mode=VIE_NEU_MODE,
        backbone_repo=VIE_NEU_BACKBONE_REPO,
        decoder_repo=VIE_NEU_CODEC_REPO,
        encoder_repo=VIE_NEU_CODEC_REPO,
        device=VIE_NEU_DEVICE,
        backend=VIE_NEU_BACKEND,
    )


def _synthesize_with_engine(engine: Any, text: str) -> bytes:
    waveform = engine.infer(text=text, show_progress=False)
    if _audio_length(waveform) == 0:
        raise TextToSpeechNoAudioError("The text-to-speech service returned no audio.")
    return _encode_mp3(waveform)


def _encode_mp3(waveform: Any) -> bytes:
    audio = io.BytesIO()
    sf.write(audio, waveform, VIE_NEU_SAMPLE_RATE, format="MP3")
    audio_bytes = audio.getvalue()
    if not audio_bytes:
        raise TextToSpeechNoAudioError("The text-to-speech service returned no audio.")
    return audio_bytes


def _audio_length(waveform: Any) -> int:
    size = getattr(waveform, "size", None)
    if isinstance(size, int):
        return size
    return len(waveform)


def _ensure_cuda_provider_available() -> None:
    if VIE_NEU_DEVICE != "cuda":
        return

    import onnxruntime as ort

    if "CUDAExecutionProvider" not in ort.get_available_providers():
        raise RuntimeError(
            "VieNeu TTS is configured for CUDA, but ONNX Runtime does not expose CUDAExecutionProvider."
        )


def _set_result_if_pending(future: asyncio.Future, value: dict[str, Any]) -> None:
    if not future.done():
        future.set_result(value)


tts_service = TextToSpeechService()
