from __future__ import annotations

import importlib.util
from pathlib import Path
import re
import subprocess
import sys


CHECKPOINT = (
    Path(__file__).resolve().parents[1]
    / "course-checkpoints"
    / "01-agent-concepts"
)
CORE_PATH = CHECKPOINT / "agent_core.py"
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def find_module_one() -> Path:
    courses_root = next(
        path
        for path in REPOSITORY_ROOT.iterdir()
        if path.is_dir() and any(child.name.endswith("-Coding-Agent") for child in path.iterdir())
    )
    main_root = next(path for path in courses_root.iterdir() if path.name.endswith("-Coding-Agent"))
    return next(path for path in main_root.iterdir() if re.search(r"01-", path.name))


def load_course_core():
    spec = importlib.util.spec_from_file_location("course_agent_core", CORE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_agent_can_finish_without_using_a_tool() -> None:
    core = load_course_core()
    llm = core.ScriptedLLM([{"type": "finish", "answer": "The task is complete."}])

    result = core.run_agent("Explain this repository", llm, tools={})

    assert result["answer"] == "The task is complete."
    assert result["finish_reason"] == "completed"
    assert result["trace"][0]["decision"]["type"] == "finish"


def test_agent_can_use_one_tool_and_then_finish() -> None:
    core = load_course_core()
    llm = core.ScriptedLLM(
        [
            {"type": "tool", "name": "read_file", "arguments": {"path": "README.md"}},
            {"type": "finish", "answer": "README inspected."},
        ]
    )

    result = core.run_agent(
        "Inspect README",
        llm,
        tools={"read_file": lambda path: f"content from {path}"},
    )

    assert result["finish_reason"] == "completed"
    assert result["trace"][0]["observation"] == {
        "status": "success",
        "tool": "read_file",
        "output": "content from README.md",
    }
    assert llm.seen_observations[1][0]["status"] == "success"


def test_tool_failure_becomes_an_observation_and_agent_can_recover() -> None:
    core = load_course_core()

    def broken_tool(path: str) -> str:
        raise OSError(f"cannot read {path}")

    llm = core.ScriptedLLM(
        [
            {"type": "tool", "name": "read_file", "arguments": {"path": "missing.md"}},
            {"type": "tool", "name": "list_files", "arguments": {}},
            {"type": "finish", "answer": "README is absent; source files are present."},
        ]
    )

    result = core.run_agent(
        "Inspect repository",
        llm,
        tools={"read_file": broken_tool, "list_files": lambda: ["main.py", "tests/"]},
    )

    assert result["finish_reason"] == "completed"
    assert result["trace"][0]["observation"]["status"] == "error"
    assert "cannot read missing.md" in result["trace"][0]["observation"]["error"]
    assert result["trace"][1]["observation"]["status"] == "success"
    assert len(llm.seen_observations[2]) == 2


def test_unknown_tool_stops_with_an_explicit_reason() -> None:
    core = load_course_core()
    llm = core.ScriptedLLM(
        [{"type": "tool", "name": "delete_world", "arguments": {}}]
    )

    result = core.run_agent("Do something unsafe", llm, tools={})

    assert result["answer"] is None
    assert result["finish_reason"] == "unknown_tool"
    assert result["trace"][0]["observation"]["status"] == "unknown_tool"


def test_max_steps_prevents_an_endless_agent_loop() -> None:
    core = load_course_core()
    llm = core.ScriptedLLM(
        [
            {"type": "tool", "name": "search", "arguments": {"query": "Agent"}},
            {"type": "tool", "name": "search", "arguments": {"query": "Agent"}},
        ]
    )

    result = core.run_agent(
        "Search forever",
        llm,
        tools={"search": lambda query: [query]},
        max_steps=1,
    )

    assert result["answer"] is None
    assert result["finish_reason"] == "max_steps"
    assert len(result["trace"]) == 1


def test_all_four_lesson_scripts_run_offline() -> None:
    scripts = sorted((CHECKPOINT / "steps").glob("l*.py"))
    assert [script.name[:3] for script in scripts] == ["l01", "l02", "l03", "l04"]

    for script in scripts:
        completed = subprocess.run(
            [sys.executable, script.name],
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


def test_module_one_lessons_meet_textbook_quality_floor() -> None:
    module = find_module_one()
    lessons = sorted(module.glob("L0[1-4]-*.md"))
    assert len(lessons) == 4

    for lesson in lessons:
        content = lesson.read_text(encoding="utf-8", errors="strict")
        assert 3_000 <= len(content) <= 15_000, lesson.name
        assert all(re.search(fr"^## {index}\.", content, re.MULTILINE) for index in range(1, 13))
        assert content.count("```") >= 6, lesson.name
        assert content.count("### ") >= 8, lesson.name
        assert "powershell" in content
        assert "ScriptedLLM" in content
        assert content.count("\uff1f") >= 5, lesson.name


def test_module_one_has_a_separate_exercise_answer_book() -> None:
    module = find_module_one()
    answer_marker = "\u53c2\u8003\u7b54\u6848"
    answer_books = [path for path in module.glob("*.md") if answer_marker in path.name]
    assert len(answer_books) == 1
    content = answer_books[0].read_text(encoding="utf-8", errors="strict")
    assert all(f"L{index:02d}" in content for index in range(1, 5))
    assert "pytest" in content
