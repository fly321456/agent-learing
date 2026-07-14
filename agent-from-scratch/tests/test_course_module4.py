from __future__ import annotations

from pathlib import Path
import re
import subprocess
import sys


CHECKPOINT = Path(__file__).resolve().parents[1] / "course-checkpoints" / "04-runtime-refactor"
PACKAGE_ROOT = CHECKPOINT / "src"


def load_runtime():
    sys.path.insert(0, str(PACKAGE_ROOT))
    try:
        import course_runtime

        return course_runtime
    finally:
        sys.path.pop(0)


def test_agent_keeps_configuration_separate_from_runner() -> None:
    runtime = load_runtime()
    llm = runtime.ScriptedLLM([runtime.LLMResponse(content="ready")])
    agent = runtime.Agent("helper", "Answer clearly.", llm, max_steps=3)

    assert agent.name == "helper"
    assert agent.max_steps == 3
    assert not hasattr(agent, "run")


def test_llm_response_describes_one_model_call() -> None:
    runtime = load_runtime()
    marker = {"vendor_item": "keep-opaque"}
    response = runtime.LLMResponse(
        tool_calls=[runtime.ToolCall("c1", "echo", {"text": "hello"})],
        continuation_items=[marker],
        finish_reason="tool_calls",
    )

    assert response.tool_calls[0].id == "c1"
    assert response.continuation_items[0] is marker
    assert not hasattr(response, "events")
    assert not hasattr(response, "tool_results")
    assert not hasattr(response, "raw_response")


def test_tool_manager_standardizes_success_unknown_and_error() -> None:
    runtime = load_runtime()

    def broken() -> str:
        raise RuntimeError("boom")

    manager = runtime.ToolManager([
        runtime.ToolSpec("echo", "Echo text.", {"type": "object"}, lambda text: text),
        runtime.ToolSpec("broken", "Fail for teaching.", {"type": "object"}, broken),
    ])

    success = manager.execute(runtime.ToolCall("c1", "echo", {"text": "hello"}))
    unknown = manager.execute(runtime.ToolCall("c2", "missing", {}))
    failed = manager.execute(runtime.ToolCall("c3", "broken", {}))

    assert (success.status, success.output) == ("success", "hello")
    assert (unknown.status, unknown.error) == ("error", "Unknown tool: missing")
    assert (failed.status, failed.error) == ("error", "boom")


def test_runner_returns_complete_result_and_ordered_events() -> None:
    runtime = load_runtime()
    continuation = {"type": "vendor_function_call", "call_id": "c1"}
    llm = runtime.ScriptedLLM([
        runtime.LLMResponse(
            tool_calls=[runtime.ToolCall("c1", "echo", {"text": "hello"})],
            continuation_items=[continuation],
            finish_reason="tool_calls",
        ),
        runtime.LLMResponse(content="final answer", finish_reason="completed"),
    ])
    agent = runtime.Agent(
        "helper",
        "Use tools when needed.",
        llm,
        tools=[runtime.ToolSpec("echo", "Echo text.", {"type": "object"}, lambda text: text)],
    )

    result = runtime.Runner().run(agent, "say hello")

    assert result.content == "final answer"
    assert result.finish_reason == "completed"
    assert result.steps == 2
    assert [item.status for item in result.tool_results] == ["success"]
    assert [event.sequence for event in result.events] == list(range(1, len(result.events) + 1))
    assert len({event.run_id for event in result.events}) == 1
    assert continuation in llm.requests[1]["messages"]
    assert any(
        item.get("type") == "function_call_output" and item.get("call_id") == "c1"
        for item in llm.requests[1]["messages"]
        if isinstance(item, dict)
    )


def test_runner_stops_at_max_steps() -> None:
    runtime = load_runtime()
    response = runtime.LLMResponse(
        tool_calls=[runtime.ToolCall("c1", "echo", {"text": "again"})],
        finish_reason="tool_calls",
    )
    llm = runtime.ScriptedLLM([response], repeat_last=True)
    agent = runtime.Agent(
        "loop",
        "Keep calling.",
        llm,
        tools=[runtime.ToolSpec("echo", "Echo text.", {"type": "object"}, lambda text: text)],
        max_steps=2,
    )

    result = runtime.Runner().run(agent, "loop")

    assert result.finish_reason == "max_steps"
    assert result.steps == 2
    assert len(result.tool_results) == 2


def test_module_four_steps_and_demo_run() -> None:
    scripts = sorted((CHECKPOINT / "steps").glob("l*.py"))
    assert [path.name[:3] for path in scripts] == ["l13", "l14", "l15", "l16"]
    for script in scripts + [CHECKPOINT / "demo.py"]:
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
        assert completed.returncode == 0, completed.stderr
        assert completed.stdout.strip()


def test_module_four_lessons_have_textbook_structure() -> None:
    repository = Path(__file__).resolve().parents[2]
    courses = next(path for path in repository.iterdir() if path.is_dir() and any(
        child.name.endswith("-Coding-Agent") for child in path.iterdir()
    ))
    main = next(path for path in courses.iterdir() if path.name.endswith("-Coding-Agent"))
    module = next(path for path in main.iterdir() if re.search(r"04-", path.name))
    lessons = sorted(path for path in module.glob("L*.md") if path.name[:3] in {
        "L13", "L14", "L15", "L16"
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
