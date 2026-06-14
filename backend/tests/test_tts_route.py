from __future__ import annotations

from fastapi.testclient import TestClient

from app.services.tts import TtsResult
from main import app


class FakeTtsService:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def synthesize(self, text: str, voice: str | None = None) -> TtsResult:
        self.calls.append(f"{text}:{voice}")
        return TtsResult(
            audio=b"wav-bytes",
            media_type="audio/wav",
        )


def test_tts_synthesizes_audio(monkeypatch) -> None:
    fake_service = FakeTtsService()
    monkeypatch.setattr("app.api.routes.tts_service", fake_service)

    client = TestClient(app)
    response = client.post("/tts", json={"text": "  Xin chao  ", "voice": "Gia Bảo"})

    assert response.status_code == 200
    assert response.content == b"wav-bytes"
    assert response.headers["content-type"] == "audio/wav"
    assert fake_service.calls == ["Xin chao:Gia Bảo"]


def test_tts_rejects_empty_text(monkeypatch) -> None:
    fake_service = FakeTtsService()
    monkeypatch.setattr("app.api.routes.tts_service", fake_service)

    client = TestClient(app)
    response = client.post("/tts", json={"text": "  "})

    assert response.status_code == 422
    assert fake_service.calls == []
