from __future__ import annotations

import asyncio
from pathlib import Path
import re
import subprocess
import sys


CHECKPOINT = Path(__file__).resolve().parents[1] / "course-checkpoints" / "08-cli-mcp-final"
PACKAGE_ROOT = CHECKPOINT / "src"


def load_product():
    sys.path.insert(0, str(PACKAGE_ROOT))
    try:
        import course_product

        return course_product
    finally:
        sys.path.pop(0)


def test_cli_formats_events_and_approval_defaults_to_deny() -> None:
    module = load_product()
    event = module.Event("tool_completed", 4, "run-1", 2, {
        "name": "run_command", "status": "success"
    })
    assert module.format_event(event) == "[2] tool <- run_command (success)"
    assert module.request_approval("run_command", {"command": ["pytest"]}, lambda _p: "") is False
    assert module.request_approval("run_command", {}, lambda _p: "yes") is True


def test_read_only_workspace_tools_block_escape(tmp_path: Path) -> None:
    module = load_product()
    (tmp_path / "README.md").write_text("Agent course\n", encoding="utf-8")
    tools = module.create_read_only_tools(tmp_path)

    assert set(tools) == {"read_workspace_file", "search_workspace"}
    assert tools["read_workspace_file"]("README.md") == "Agent course\n"
    assert "README.md:1:Agent course" in tools["search_workspace"]("Agent")
    try:
        tools["read_workspace_file"]("../outside.md")
    except ValueError as exc:
        assert "outside" in str(exc).lower()
    else:
        raise AssertionError("MCP read escaped the workspace")


def test_fastmcp_server_exposes_only_read_only_tools(tmp_path: Path) -> None:
    module = load_product()
    server = module.create_mcp_server(tmp_path)
    tools = asyncio.run(server.list_tools())
    assert {tool.name for tool in tools} == {"read_workspace_file", "search_workspace"}


def test_checkpoint_builds_wheel_and_supports_editable_install(tmp_path: Path) -> None:
    wheel_dir = tmp_path / "wheel"
    built = subprocess.run(
        [sys.executable, "-m", "pip", "wheel", ".", "--no-deps", "--no-build-isolation", "-w", str(wheel_dir)],
        cwd=CHECKPOINT, capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=60, check=False,
    )
    assert built.returncode == 0, built.stdout + built.stderr
    assert len(list(wheel_dir.glob("course_product-*.whl"))) == 1

    target = tmp_path / "editable"
    installed = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-e", ".", "--no-deps", "--no-build-isolation", "--target", str(target)],
        cwd=CHECKPOINT, capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=60, check=False,
    )
    assert installed.returncode == 0, installed.stdout + installed.stderr
    assert any(path.name.startswith("__editable__") for path in target.iterdir())


def test_module_eight_steps_and_demo_run() -> None:
    scripts = sorted((CHECKPOINT / "steps").glob("l*.py"))
    assert [path.name[:3] for path in scripts] == ["l29", "l30", "l31", "l32"]
    for script in scripts + [CHECKPOINT / "demo.py"]:
        completed = subprocess.run(
            [sys.executable, str(script)], cwd=script.parent, capture_output=True,
            text=True, encoding="utf-8", errors="strict", timeout=20, check=False,
        )
        assert completed.returncode == 0, completed.stderr
        assert completed.stdout.strip()


def test_module_eight_lessons_have_textbook_structure() -> None:
    repository = Path(__file__).resolve().parents[2]
    courses = next(path for path in repository.iterdir() if path.is_dir() and any(
        child.name.endswith("-Coding-Agent") for child in path.iterdir()
    ))
    main = next(path for path in courses.iterdir() if path.name.endswith("-Coding-Agent"))
    module = next(path for path in main.iterdir() if re.search(r"08-", path.name))
    lessons = sorted(path for path in module.glob("L*.md") if path.name[:3] in {
        "L29", "L30", "L31", "L32"
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
