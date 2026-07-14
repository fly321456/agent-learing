from __future__ import annotations

from pathlib import Path
import re
import subprocess
import sys


CHECKPOINT = Path(__file__).resolve().parents[1] / "course-checkpoints" / "05-coding-tools"
PACKAGE_ROOT = CHECKPOINT / "src"


def load_tools():
    sys.path.insert(0, str(PACKAGE_ROOT))
    try:
        import course_tools

        return course_tools
    finally:
        sys.path.pop(0)


def test_read_file_supports_utf8_and_blocks_outside_workspace(tmp_path: Path) -> None:
    tools = load_tools()
    (tmp_path / "notes.md").write_text("第一行\n第二行\n", encoding="utf-8")
    context = tools.ToolContext(tmp_path)

    assert tools.read_file(context=context, path="notes.md", start_line=2) == "第二行\n"
    try:
        tools.read_file(context=context, path="../outside.md")
    except tools.WorkspaceBoundaryError as exc:
        assert "outside" in str(exc).lower()
    else:
        raise AssertionError("outside path was not blocked")


def test_search_files_limits_results_and_skips_binary(tmp_path: Path) -> None:
    tools = load_tools()
    (tmp_path / "a.py").write_text("needle = 1\nneedle = 2\n", encoding="utf-8")
    (tmp_path / "b.py").write_text("needle = 3\n", encoding="utf-8")
    (tmp_path / "binary.bin").write_bytes(b"\xff\xfe\x00")

    output = tools.search_files(
        context=tools.ToolContext(tmp_path), query="needle", glob="*.py", max_results=2
    )

    assert output.count("needle") == 2
    assert "result limit reached" in output


def test_patch_requires_unique_match_and_approval(tmp_path: Path) -> None:
    tools = load_tools()
    source = tmp_path / "app.py"
    source.write_text("value = 1\nvalue = 1\n", encoding="utf-8")
    spec = tools.create_coding_tools()[2]
    manager = tools.ToolManager([spec])

    denied = manager.execute(
        tools.ToolCall("c1", "apply_patch", {
            "path": "app.py", "old_text": "value = 1", "new_text": "value = 2"
        }),
        tools.ToolContext(tmp_path, approval=lambda _spec, _args: False),
    )
    ambiguous = manager.execute(
        tools.ToolCall("c2", "apply_patch", {
            "path": "app.py", "old_text": "value = 1", "new_text": "value = 2"
        }),
        tools.ToolContext(tmp_path, approval=lambda _spec, _args: True),
    )

    assert denied.status == "denied"
    assert ambiguous.status == "error"
    assert "not unique" in (ambiguous.error or "")
    assert source.read_text(encoding="utf-8") == "value = 1\nvalue = 1\n"


def test_command_reports_nonzero_and_timeout(tmp_path: Path) -> None:
    tools = load_tools()
    command = next(spec for spec in tools.create_coding_tools() if spec.name == "run_command")
    manager = tools.ToolManager([command])
    approval = lambda _spec, _args: True

    failed = manager.execute(
        tools.ToolCall("c1", "run_command", {
            "command": [sys.executable, "-c", "import sys; print('bad'); sys.exit(3)"]
        }),
        tools.ToolContext(tmp_path, approval=approval, command_timeout=2),
    )
    timed_out = manager.execute(
        tools.ToolCall("c2", "run_command", {
            "command": [sys.executable, "-c", "import time; time.sleep(1)"]
        }),
        tools.ToolContext(tmp_path, approval=approval, command_timeout=0.3),
    )

    assert (failed.status, failed.exit_code) == ("error", 3)
    assert "bad" in failed.output
    assert timed_out.status == "timeout"


def test_module_five_steps_and_demo_run() -> None:
    scripts = sorted((CHECKPOINT / "steps").glob("l*.py"))
    assert [path.name[:3] for path in scripts] == ["l17", "l18", "l19", "l20"]
    for script in scripts + [CHECKPOINT / "demo.py"]:
        completed = subprocess.run(
            [sys.executable, str(script)], cwd=script.parent, capture_output=True,
            text=True, encoding="utf-8", errors="strict", timeout=10, check=False,
        )
        assert completed.returncode == 0, completed.stderr
        assert completed.stdout.strip()


def test_module_five_lessons_have_textbook_structure() -> None:
    repository = Path(__file__).resolve().parents[2]
    courses = next(path for path in repository.iterdir() if path.is_dir() and any(
        child.name.endswith("-Coding-Agent") for child in path.iterdir()
    ))
    main = next(path for path in courses.iterdir() if path.name.endswith("-Coding-Agent"))
    module = next(path for path in main.iterdir() if re.search(r"05-", path.name))
    lessons = sorted(path for path in module.glob("L*.md") if path.name[:3] in {
        "L17", "L18", "L19", "L20"
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
