from pathlib import Path

from agent_from_scratch.schemas import ToolCall
from agent_from_scratch.tools import ToolContext, ToolManager, create_default_tools


def test_coding_tools_complete_a_small_repository_change(tmp_path: Path) -> None:
    source = tmp_path / "calculator.py"
    source.write_text("def add(a, b):\n    return a - b\n", encoding="utf-8")
    context = ToolContext(workspace=tmp_path, approval=lambda _tool, _arguments: True)
    manager = ToolManager(create_default_tools())

    read = manager.execute(
        ToolCall("read-1", "read_file", {"path": "calculator.py"}), context
    )
    search = manager.execute(
        ToolCall(
            "search-1",
            "search_files",
            {"query": "return a - b", "glob": "*.py"},
        ),
        context,
    )
    patch = manager.execute(
        ToolCall(
            "patch-1",
            "apply_patch",
            {
                "path": "calculator.py",
                "old_text": "return a - b",
                "new_text": "return a + b",
            },
        ),
        context,
    )
    check = manager.execute(
        ToolCall(
            "command-1",
            "run_command",
            {
                "command": [
                    "python",
                    "-c",
                    "from calculator import add; assert add(2, 3) == 5",
                ]
            },
        ),
        context,
    )

    assert read.status == "success"
    assert search.status == "success"
    assert "calculator.py" in search.output
    assert patch.status == "success"
    assert check.status == "success"
    assert "return a + b" in source.read_text(encoding="utf-8")
