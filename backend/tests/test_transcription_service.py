from __future__ import annotations

import shutil
import subprocess
import threading

import pytest

import transcription_service
from transcription_service import AudioTranscriptionError, BackendTranscriptionError


def test_read_audio_samples_falls_back_to_ffmpeg_for_compressed_audio(
    monkeypatch,
    tmp_path,
):
    import numpy as np
    import soundfile as sf

    audio_path = tmp_path / "android-recording.m4a"
    audio_path.write_bytes(b"compressed-audio")
    expected_samples = np.array([0.0, 0.25, -0.25], dtype=np.float32)
    calls = []

    def fake_read(file_path, dtype):
        assert file_path == str(audio_path)
        assert dtype == "float32"
        raise sf.LibsndfileError(1, prefix="Error opening test audio: ")

    def fake_run(command, check, capture_output, timeout):
        calls.append(command)
        assert check is True
        assert capture_output is True
        assert timeout == transcription_service.FFMPEG_DECODE_TIMEOUT_SECONDS
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=expected_samples.tobytes(),
            stderr=b"",
        )

    monkeypatch.setattr(sf, "read", fake_read)
    monkeypatch.setattr(transcription_service.subprocess, "run", fake_run)

    samples, sample_rate, duration_seconds = transcription_service._read_audio_samples(
        str(audio_path)
    )

    assert sample_rate == transcription_service.SAMPLE_RATE
    assert duration_seconds == pytest.approx(3 / transcription_service.SAMPLE_RATE)
    assert "-i" in calls[0]
    assert str(audio_path) in calls[0]
    np.testing.assert_array_equal(samples, expected_samples)


def test_ffmpeg_missing_is_backend_error(monkeypatch, tmp_path):
    import soundfile as sf

    audio_path = tmp_path / "android-recording.m4a"
    audio_path.write_bytes(b"compressed-audio")

    def fake_read(file_path, dtype):
        raise sf.LibsndfileError(1, prefix="Error opening test audio: ")

    def fake_run(command, check, capture_output, timeout):
        raise FileNotFoundError

    monkeypatch.setattr(sf, "read", fake_read)
    monkeypatch.setattr(transcription_service.subprocess, "run", fake_run)

    with pytest.raises(BackendTranscriptionError, match="ffmpeg"):
        transcription_service._read_audio_samples(str(audio_path))


def test_ffmpeg_timeout_is_audio_error(monkeypatch, tmp_path):
    audio_path = tmp_path / "android-recording.m4a"
    audio_path.write_bytes(b"compressed-audio")

    def fake_run(command, check, capture_output, timeout):
        raise subprocess.TimeoutExpired(command, timeout)

    monkeypatch.setattr(transcription_service.subprocess, "run", fake_run)

    with pytest.raises(AudioTranscriptionError, match="too long"):
        transcription_service._read_audio_samples_with_ffmpeg(str(audio_path))


def test_ffmpeg_rejects_large_compressed_audio(monkeypatch, tmp_path):
    audio_path = tmp_path / "android-recording.m4a"
    audio_path.write_bytes(b"compressed-audio")
    monkeypatch.setattr(transcription_service.os.path, "getsize", lambda file_path: 26 * 1024 * 1024)

    with pytest.raises(AudioTranscriptionError, match="too large"):
        transcription_service._read_audio_samples_with_ffmpeg(str(audio_path))


def test_read_audio_samples_decodes_real_m4a(tmp_path):
    if shutil.which("ffmpeg") is None:
        pytest.skip("ffmpeg is required for compressed mobile audio")

    audio_path = tmp_path / "android-recording.m4a"
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:duration=0.1",
            "-c:a",
            "aac",
            "-y",
            str(audio_path),
        ],
        check=True,
    )

    samples, sample_rate, duration_seconds = transcription_service._read_audio_samples(
        str(audio_path)
    )

    assert sample_rate == transcription_service.SAMPLE_RATE
    assert duration_seconds > 0
    assert samples.size > 0


def test_asr_worker_returns_audio_errors_without_crashing(monkeypatch):
    parent_connection, worker_connection = transcription_service.Pipe()

    class FailingModel:
        def load_model(self):
            return None

        def transcribe(self, file_path, language):
            raise AudioTranscriptionError("Uploaded audio could not be decoded.")

    monkeypatch.setattr(transcription_service, "_LocalTranscriptionModel", FailingModel)

    worker = threading.Thread(
        target=transcription_service._run_asr_worker,
        args=(worker_connection,),
    )
    worker.start()

    assert parent_connection.recv() == {"ready": True}
    parent_connection.send({
        "cmd": "RUN",
        "file_path": "android-recording.m4a",
        "language": "vi",
    })

    assert parent_connection.recv() == {
        "error": {
            "type": "audio",
            "message": "Uploaded audio could not be decoded.",
        },
    }
    assert worker.is_alive()

    parent_connection.send({"cmd": "STOP"})
    worker.join(timeout=1)
    parent_connection.close()

    assert not worker.is_alive()


def test_asr_worker_returns_backend_errors_without_crashing(monkeypatch):
    parent_connection, worker_connection = transcription_service.Pipe()

    class FailingModel:
        def load_model(self):
            return None

        def transcribe(self, file_path, language):
            raise BackendTranscriptionError("Compressed audio requires ffmpeg.")

    monkeypatch.setattr(transcription_service, "_LocalTranscriptionModel", FailingModel)

    worker = threading.Thread(
        target=transcription_service._run_asr_worker,
        args=(worker_connection,),
    )
    worker.start()

    assert parent_connection.recv() == {"ready": True}
    parent_connection.send({
        "cmd": "RUN",
        "file_path": "android-recording.m4a",
        "language": "vi",
    })

    assert parent_connection.recv() == {
        "error": {
            "type": "backend",
            "message": "Compressed audio requires ffmpeg.",
        },
    }
    assert worker.is_alive()

    parent_connection.send({"cmd": "STOP"})
    worker.join(timeout=1)
    parent_connection.close()

    assert not worker.is_alive()


def test_result_from_worker_message_maps_worker_audio_errors():
    with pytest.raises(AudioTranscriptionError, match="could not be decoded"):
        transcription_service._result_from_worker_message({
            "error": {
                "type": "audio",
                "message": "Uploaded audio could not be decoded.",
            },
        })


def test_result_from_worker_message_maps_worker_backend_errors():
    with pytest.raises(BackendTranscriptionError, match="failed"):
        transcription_service._result_from_worker_message({
            "error": {
                "type": "backend",
                "message": "ASR worker failed.",
            },
        })
