from __future__ import annotations

from pathlib import Path
import re
import subprocess
import sys


CHECKPOINT = Path(__file__).resolve().parents[1] / "course-checkpoints" / "06-session-reliability"
PACKAGE_ROOT = CHECKPOINT / "src"


def load_runtime():
    sys.path.insert(0, str(PACKAGE_ROOT))
    try:
        import course_reliability

        return course_reliability
    finally:
        sys.path.pop(0)


def test_session_round_trips_utf8_and_tracks_turns(tmp_path: Path) -> None:
    runtime = load_runtime()
    session = runtime.Session("session-1")
    turn = session.start_turn("读取课程")
    session.append_assistant(turn.id, "可以")
    store = runtime.SessionStore(tmp_path / "sessions")

    store.save(session)
    restored = store.load("session-1")

    assert restored == session
    assert restored.messages[0].turn_id == turn.id
    assert restored.messages[0].role == "user"
    assert restored.messages[1].role == "assistant"


def test_context_window_keeps_complete_recent_messages_and_summary() -> None:
    runtime = load_runtime()
    messages = [
        runtime.Message("user", "old-" + "a" * 30, "turn-1"),
        runtime.Message("assistant", "middle-" + "b" * 20, "turn-1"),
        runtime.Message("user", "latest", "turn-2"),
    ]

    result = runtime.ContextWindow(max_chars=25).build(messages, summary="Earlier: inspected config")

    assert result.truncated is True
    assert result.messages[0].role == "system"
    assert "Earlier: inspected config" in result.messages[0].content
    assert result.messages[-1].content == "latest"
    assert all(message.content != "middle-" + "b" * 20 for message in result.messages)


def test_checkpoint_round_trip_prevents_repeating_completed_side_effect(tmp_path: Path) -> None:
    runtime = load_runtime()
    store = runtime.CheckpointStore(tmp_path / "checkpoints")
    checkpoint = runtime.RunCheckpoint("run-1", next_step=2)
    calls = 0

    def side_effect() -> str:
        nonlocal calls
        calls += 1
        return "patched"

    first = runtime.execute_once(checkpoint, "call-1", side_effect)
    store.save(checkpoint)
    restored = store.load("run-1")
    second = runtime.execute_once(restored, "call-1", side_effect)

    assert first == second == "patched"
    assert calls == 1
    assert restored.completed_calls == {"call-1": "patched"}


def test_retry_policy_retries_only_retryable_errors() -> None:
    runtime = load_runtime()
    attempts = 0

    def flaky() -> str:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise runtime.RetryableError("temporary")
        return "recovered"

    events: list[dict] = []
    assert runtime.RetryPolicy(attempts=2, base_delay=0).run(flaky, events.append) == "recovered"
    assert attempts == 2
    assert events == [{"type": "retry", "attempt": 1, "error": "temporary"}]

    deterministic_calls = 0

    def invalid() -> str:
        nonlocal deterministic_calls
        deterministic_calls += 1
        raise runtime.DeterministicError("invalid response")

    try:
        runtime.RetryPolicy(attempts=3, base_delay=0).run(invalid)
    except runtime.DeterministicError:
        pass
    else:
        raise AssertionError("deterministic error was swallowed")
    assert deterministic_calls == 1


def test_runtime_config_validates_values() -> None:
    runtime = load_runtime()
    config = runtime.RuntimeConfig.from_mapping({
        "AGENT_MAX_STEPS": "4",
        "AGENT_CONTEXT_CHARS": "1200",
        "AGENT_RETRY_ATTEMPTS": "2",
    })
    assert (config.max_steps, config.context_chars, config.retry_attempts) == (4, 1200, 2)
    try:
        runtime.RuntimeConfig.from_mapping({"AGENT_MAX_STEPS": "0"})
    except ValueError as exc:
        assert "max_steps" in str(exc)
    else:
        raise AssertionError("invalid config was accepted")


def test_module_six_steps_and_demo_run() -> None:
    scripts = sorted((CHECKPOINT / "steps").glob("l*.py"))
    assert [path.name[:3] for path in scripts] == ["l21", "l22", "l23", "l24"]
    for script in scripts + [CHECKPOINT / "demo.py"]:
        completed = subprocess.run(
            [sys.executable, str(script)], cwd=script.parent, capture_output=True,
            text=True, encoding="utf-8", errors="strict", timeout=10, check=False,
        )
        assert completed.returncode == 0, completed.stderr
        assert completed.stdout.strip()


def test_module_six_lessons_have_textbook_structure() -> None:
    repository = Path(__file__).resolve().parents[2]
    courses = next(path for path in repository.iterdir() if path.is_dir() and any(
        child.name.endswith("-Coding-Agent") for child in path.iterdir()
    ))
    main = next(path for path in courses.iterdir() if path.name.endswith("-Coding-Agent"))
    module = next(path for path in main.iterdir() if re.search(r"06-", path.name))
    lessons = sorted(path for path in module.glob("L*.md") if path.name[:3] in {
        "L21", "L22", "L23", "L24"
    })
    assert len(lessons) == 4
    for lesson in lessons:
        content = lesson.read_text(encoding="utf-8", errors="strict")
        assert 3_500 <= len(content) <= 15_000, lesson.name
        assert all(re.search(fr"^## {index}\.", content, re.MULTILINE) for index in range(1, 13))
        assert content.count("```") >= 6
        assert content.count("\uff1f") >= 5
    marker = "\u53c2\u8003\u7b54\u6848"
    assert len([path for path in module.glob("*.md") if marker in path.name]) == 1
