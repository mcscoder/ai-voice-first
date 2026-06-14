from __future__ import annotations

import anyio

import main


def test_lifespan_loads_asr_model_on_startup(monkeypatch) -> None:
    class FakeAsrService:
        def __init__(self) -> None:
            self.loaded = False

        def load_model(self) -> object:
            self.loaded = True
            return object()

    fake_service = FakeAsrService()
    monkeypatch.setattr(main, "asr_service", fake_service)

    async def run_lifespan() -> None:
        async with main.lifespan(main.app):
            pass

    anyio.run(run_lifespan)

    assert fake_service.loaded is True
