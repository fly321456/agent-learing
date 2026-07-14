from __future__ import annotations

import importlib.util
from pathlib import Path
import re
import subprocess
import sys


CHECKPOINT = Path(__file__).resolve().parents[1] / "course-checkpoints" / "03-agent-loop"


def load_core():
    path = CHECKPOINT / "agent_loop.py"
    spec = importlib.util.spec_from_file_location("course_agent_loop", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_text_response_finishes_without_tool() -> None:
    core = load_core()
    result = core.run_agent("hello", core.ScriptedModel([core.ModelResponse("ready")]), {})
    assert result["answer"] == "ready"
    assert result["finish_reason"] == "completed"
    assert result["tool_results"] == []


def test_single_and_same_round_multiple_tools() -> None:
    core = load_core()
    model = core.ScriptedModel([
        core.ModelResponse(tool_calls=[
            core.ToolCall("c1", "calculator", {"expression": "6 * 7"}),
            core.ToolCall("c2", "current_time", {}),
        ]),
        core.ModelResponse("done"),
    ])
    result = core.run_agent(
        "calculate and tell time",
        model,
        {"calculator": lambda expression: "42", "current_time": lambda: "12:00"},
    )
    assert [item["output"] for item in result["tool_results"]] == ["42", "12:00"]
    assert result["steps"] == 2


def test_invalid_unknown_and_failed_tools_become_observations() -> None:
    core = load_core()

    def broken() -> str:
        raise RuntimeError("boom")

    model = core.ScriptedModel([
        core.ModelResponse(tool_calls=[
            core.ToolCall("bad", "calculator", "not-an-object"),
            core.ToolCall("missing", "missing_tool", {}),
            core.ToolCall("broken", "broken", {}),
        ]),
        core.ModelResponse("errors observed"),
    ])
    result = core.run_agent("test errors", model, {"calculator": lambda **kw: "x", "broken": broken})
    assert [item["status"] for item in result["tool_results"]] == [
        "invalid_arguments", "unknown_tool", "error"
    ]
    assert result["finish_reason"] == "completed"


def test_max_steps_stops_repeating_model() -> None:
    core = load_core()
    response = core.ModelResponse(tool_calls=[core.ToolCall("c", "ping", {})])
    result = core.run_agent(
        "loop", core.ScriptedModel([response], repeat_last=True), {"ping": lambda: "pong"}, max_steps=2
    )
    assert result["finish_reason"] == "max_steps"
    assert result["steps"] == 2


def test_module_three_steps_and_demo_run() -> None:
    scripts = sorted((CHECKPOINT / "steps").glob("l*.py"))
    assert [path.name[:3] for path in scripts] == ["l09", "l10", "l11", "l12"]
    for script in scripts + [CHECKPOINT / "demo.py"]:
        completed = subprocess.run(
            [sys.executable, str(script)], cwd=script.parent, capture_output=True,
            text=True, encoding="utf-8", errors="strict", timeout=10, check=False,
        )
        assert completed.returncode == 0, completed.stderr
        assert completed.stdout.strip()


def test_module_three_lessons_have_textbook_structure() -> None:
    repository = Path(__file__).resolve().parents[2]
    courses = next(path for path in repository.iterdir() if path.is_dir() and any(
        child.name.endswith("-Coding-Agent") for child in path.iterdir()))
    main = next(path for path in courses.iterdir() if path.name.endswith("-Coding-Agent"))
    module = next(path for path in main.iterdir() if re.search(r"03-", path.name))
    lessons = sorted(module.glob("L(0[9]|1[0-2])-*.md"))
    if not lessons:
        lessons = sorted(path for path in module.glob("L*.md") if path.name[:3] in {"L09", "L10", "L11", "L12"})
    assert len(lessons) == 4
    for lesson in lessons:
        content = lesson.read_text(encoding="utf-8", errors="strict")
        assert 3_500 <= len(content) <= 15_000, lesson.name
        assert all(re.search(fr"^## {index}\.", content, re.MULTILINE) for index in range(1, 13))
        assert content.count("```") >= 6
        assert content.count("\uff1f") >= 5

    marker = "\u53c2\u8003\u7b54\u6848"
    assert len([path for path in module.glob("*.md") if marker in path.name]) == 1
