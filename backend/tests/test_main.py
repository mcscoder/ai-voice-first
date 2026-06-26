import main


def test_main_sets_graceful_shutdown_timeout(monkeypatch) -> None:
    calls: dict[str, object] = {}

    def run(app: object, **kwargs: object) -> None:
        calls["app"] = app
        calls["kwargs"] = kwargs

    monkeypatch.setattr("uvicorn.run", run)

    main.main()

    assert calls == {
        "app": main.app,
        "kwargs": {
            "host": main.config.host,
            "port": main.config.port,
            "timeout_graceful_shutdown": 5,
        },
    }
