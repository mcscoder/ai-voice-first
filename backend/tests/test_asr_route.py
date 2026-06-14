from __future__ import annotations

from fastapi.testclient import TestClient

from app.services.asr import AsrResult
from main import app


class FakeAsrService:
    def __init__(self) -> None:
        self.calls: list[tuple[bytes, str | None]] = []

    def transcribe(
        self,
        audio: bytes,
        language: str | None = None,
    ) -> AsrResult:
        self.calls.append((audio, language))
        return AsrResult(
            text="hello world",
            language=language or "English",
            model="Qwen/Qwen3-ASR-0.6B",
        )


def test_asr_upload_transcribes_audio(monkeypatch) -> None:
    fake_service = FakeAsrService()
    monkeypatch.setattr("app.api.routes.asr_service", fake_service)

    client = TestClient(app)
    response = client.post(
        "/asr",
        data={"language": "English"},
        files={"file": ("speech.wav", b"audio", "audio/wav")},
    )

    assert response.status_code == 200
    assert response.json() == {
        "text": "hello world",
        "language": "English",
        "model": "Qwen/Qwen3-ASR-0.6B",
        "filename": "speech.wav",
        "content_type": "audio/wav",
    }
    assert fake_service.calls
    assert fake_service.calls[0][0] == b"audio"
    assert fake_service.calls[0][1] == "English"


def test_asr_accepts_vietnamese_language_code(monkeypatch) -> None:
    fake_service = FakeAsrService()
    monkeypatch.setattr("app.api.routes.asr_service", fake_service)

    client = TestClient(app)
    response = client.post(
        "/asr",
        data={"language": "vi"},
        files={"file": ("speech.wav", b"audio", "audio/wav")},
    )

    assert response.status_code == 200
    assert fake_service.calls[0][1] == "vi"


def test_asr_rejects_empty_upload(monkeypatch) -> None:
    fake_service = FakeAsrService()
    monkeypatch.setattr("app.api.routes.asr_service", fake_service)

    client = TestClient(app)
    response = client.post(
        "/asr",
        files={"file": ("empty.wav", b"", "audio/wav")},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Uploaded file is empty."}
    assert fake_service.calls == []
