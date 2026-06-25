import json

from app.services.assistant.telemetry import AssistantTelemetry


def test_telemetry_moves_completed_run_to_recent_history() -> None:
    telemetry = AssistantTelemetry(max_recent_runs=2)

    run_id = telemetry.start_run("en")
    telemetry.start_stage(run_id, "asr")
    telemetry.finish_stage(
        run_id,
        "asr",
        {
            "transcript": "Hello",
            "language": "English",
            "model": "test",
        },
    )
    telemetry.finish_stage_with_duration(
        run_id,
        "llm_response_stream",
        42.5,
        {"characters": 12},
    )
    telemetry.complete_run(run_id)

    snapshot = telemetry.snapshot()

    assert snapshot["summary"] == {"active_count": 0, "recent_count": 1}
    recent_run = snapshot["recent_runs"][0]
    assert recent_run["run_id"] == run_id
    assert recent_run["status"] == "done"
    assert recent_run["metadata"] == {"language": "en"}

    stages = {stage["name"]: stage for stage in recent_run["stages"]}
    assert stages["asr"]["status"] == "done"
    assert stages["asr"]["metadata"]["transcript"] == "Hello"
    assert stages["llm_response_stream"]["duration_ms"] == 42.5
    assert stages["llm_response_stream"]["metadata"] == {"characters": 12}


def test_telemetry_keeps_bounded_recent_history() -> None:
    telemetry = AssistantTelemetry(max_recent_runs=2)

    first = telemetry.start_run("en")
    telemetry.complete_run(first)
    second = telemetry.start_run("vi")
    telemetry.complete_run(second)
    third = telemetry.start_run("en")
    telemetry.complete_run(third)

    snapshot = telemetry.snapshot()

    assert [run["run_id"] for run in snapshot["recent_runs"]] == [third, second]


def test_telemetry_subscriber_receives_initial_snapshot_and_updates() -> None:
    telemetry = AssistantTelemetry(max_recent_runs=2)
    subscriber = telemetry.subscribe(keepalive_seconds=0.01)

    initial_snapshot = next(subscriber)
    assert initial_snapshot["summary"] == {"active_count": 0, "recent_count": 0}

    run_id = telemetry.start_run("en")
    update = next(subscriber)

    assert update["summary"] == {"active_count": 1, "recent_count": 0}
    assert update["active_runs"][0]["run_id"] == run_id

    subscriber.close()


def test_telemetry_subscriber_keeps_latest_snapshot_for_slow_consumers() -> None:
    telemetry = AssistantTelemetry(max_recent_runs=2)
    subscriber = telemetry.subscribe(keepalive_seconds=0.01)
    next(subscriber)

    run_id = telemetry.start_run("en")
    telemetry.start_stage(run_id, "asr")
    telemetry.finish_stage(run_id, "asr", {"transcript": "Hello"})

    update = next(subscriber)
    stages = {stage["name"]: stage for stage in update["active_runs"][0]["stages"]}

    assert stages["asr"]["status"] == "done"
    assert stages["asr"]["metadata"] == {"transcript": "Hello"}

    subscriber.close()


def test_telemetry_formats_payload_and_sse_event() -> None:
    telemetry = AssistantTelemetry(max_recent_runs=2)
    snapshot = telemetry.snapshot()

    payload = telemetry.payload(snapshot)
    event = telemetry.sse_event(snapshot)

    assert payload["services"]["llm_model"] == "deepseek-v4-flash"
    assert payload["services"]["llm_thinking"] == "disabled"
    lines = event.splitlines()
    assert lines[0] == "event: telemetry"
    assert json.loads(lines[1].removeprefix("data: "))["services"] == payload["services"]
