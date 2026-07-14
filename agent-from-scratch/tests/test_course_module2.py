from __future__ import annotations

import importlib.util
from pathlib import Path
import re
import subprocess
import sys


CHECKPOINT = Path(__file__).resolve().parents[1] / "course-checkpoints" / "02-tool-calling"
CORE_PATH = CHECKPOINT / "responses_core.py"


def load_core():
    spec = importlib.util.spec_from_file_location("course_responses_core", CORE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_text_request_keeps_instructions_separate_from_user_input() -> None:
    core = load_core()
    client = core.ScriptedResponsesClient([core.ScriptedResponse(output_text="concise")])

    text = core.generate_text(client, "course-model", "Be concise.", "Explain Agent.")

    assert text == "concise"
    assert client.requests == [
        {
            "model": "course-model",
            "instructions": "Be concise.",
            "input": "Explain Agent.",
        }
    ]


def test_function_schema_is_closed_and_strict() -> None:
    core = load_core()

    schema = core.time_tool_schema()

    assert schema["type"] == "function"
    assert schema["name"] == "get_current_time"
    assert schema["strict"] is True
    assert schema["parameters"]["additionalProperties"] is False


def test_fixed_round_trip_preserves_output_and_call_id() -> None:
    core = load_core()
    call = core.ResponseItem(
        type="function_call",
        call_id="call-17",
        name="get_current_time",
        arguments="{}",
    )
    client = core.ScriptedResponsesClient(
        [
            core.ScriptedResponse(output=[call]),
            core.ScriptedResponse(output_text="The current time is 09:30."),
        ]
    )

    result = core.run_fixed_tool_round_trip(
        client,
        model="course-model",
        user_input="What time is it?",
        tool_handlers={"get_current_time": lambda: "2026-07-14T09:30:00+08:00"},
    )

    assert result["answer"] == "The current time is 09:30."
    second_input = client.requests[1]["input"]
    assert second_input[1] is call
    assert second_input[2] == {
        "type": "function_call_output",
        "call_id": "call-17",
        "output": "2026-07-14T09:30:00+08:00",
    }


def test_invalid_function_arguments_are_reported_without_executing_tool() -> None:
    core = load_core()
    called = False

    def handler() -> str:
        nonlocal called
        called = True
        return "never"

    client = core.ScriptedResponsesClient(
        [
            core.ScriptedResponse(
                output=[
                    core.ResponseItem(
                        type="function_call",
                        call_id="bad-json",
                        name="get_current_time",
                        arguments="{",
                    )
                ]
            ),
            core.ScriptedResponse(output_text="The tool arguments were invalid."),
        ]
    )

    result = core.run_fixed_tool_round_trip(
        client,
        model="course-model",
        user_input="What time is it?",
        tool_handlers={"get_current_time": handler},
    )

    assert called is False
    assert result["tool_outputs"][0]["output"].startswith("error: invalid JSON")


def test_module_two_steps_and_demo_run_offline() -> None:
    scripts = sorted((CHECKPOINT / "steps").glob("l*.py"))
    assert [path.name[:3] for path in scripts] == ["l05", "l06", "l07", "l08"]
    scripts.append(CHECKPOINT / "demo.py")

    for script in scripts:
        completed = subprocess.run(
            [sys.executable, str(script)],
            cwd=script.parent,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="strict",
            timeout=10,
            check=False,
        )
        assert completed.returncode == 0, f"{script.name}: {completed.stderr}"
        assert completed.stdout.strip()


def test_module_two_lessons_have_textbook_structure() -> None:
    repository = Path(__file__).resolve().parents[2]
    courses = next(
        path for path in repository.iterdir()
        if path.is_dir() and any(child.name.endswith("-Coding-Agent") for child in path.iterdir())
    )
    main = next(path for path in courses.iterdir() if path.name.endswith("-Coding-Agent"))
    module = next(path for path in main.iterdir() if re.search(r"02-", path.name))
    lessons = sorted(module.glob("L0[5-8]-*.md"))
    assert len(lessons) == 4
    for lesson in lessons:
        content = lesson.read_text(encoding="utf-8", errors="strict")
        assert 3_500 <= len(content) <= 15_000, lesson.name
        assert all(re.search(fr"^## {index}\.", content, re.MULTILINE) for index in range(1, 13))
        assert content.count("```") >= 6
        assert content.count("\uff1f") >= 5
        assert "2026-07-14" in content

    answer_marker = "\u53c2\u8003\u7b54\u6848"
    answers = [path for path in module.glob("*.md") if answer_marker in path.name]
    assert len(answers) == 1
