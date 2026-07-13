import sys

from agent_from_scratch.schemas import ToolCall
from agent_from_scratch.tools import ToolContext, ToolManager, create_default_tools


def manager():
    return ToolManager(create_default_tools())


def test_read_file_and_search_files_stay_inside_workspace(tmp_path):
    source = tmp_path / "src" / "demo.py"
    source.parent.mkdir()
    source.write_text("needle = 42\n", encoding="utf-8")
    context = ToolContext(workspace=tmp_path)

    read_result = manager().execute(
        ToolCall("read-1", "read_file", {"path": "src/demo.py"}), context
    )
    search_result = manager().execute(
        ToolCall("search-1", "search_files", {"query": "needle", "path": "src"}), context
    )
    outside_result = manager().execute(
        ToolCall("read-2", "read_file", {"path": "../outside.txt"}), context
    )

    assert read_result.status == "success"
    assert read_result.output == "needle = 42\n"
    assert search_result.status == "success"
    assert "src/demo.py:1:needle = 42" in search_result.output
    assert outside_result.status == "error"
    assert "outside the workspace" in outside_result.error


def test_apply_patch_requires_approval_and_replaces_exact_text(tmp_path):
    target = tmp_path / "demo.txt"
    target.write_text("old value\n", encoding="utf-8")
    call = ToolCall(
        "patch-1",
        "apply_patch",
        {"path": "demo.txt", "old_text": "old value", "new_text": "new value"},
    )

    denied = manager().execute(call, ToolContext(workspace=tmp_path))
    approved = manager().execute(
        call,
        ToolContext(workspace=tmp_path, approval=lambda _tool, _arguments: True),
    )

    assert denied.status == "denied"
    assert approved.status == "success"
    assert target.read_text(encoding="utf-8") == "new value\n"


def test_unknown_tool_and_command_timeout_are_structured_results(tmp_path):
    unknown = manager().execute(
        ToolCall("missing-1", "missing_tool", {}), ToolContext(workspace=tmp_path)
    )
    timeout = manager().execute(
        ToolCall(
            "command-1",
            "run_command",
            {"command": [sys.executable, "-c", "import time; time.sleep(0.2)"]},
        ),
        ToolContext(
            workspace=tmp_path,
            approval=lambda _tool, _arguments: True,
            command_timeout=0.01,
        ),
    )

    assert unknown.status == "error"
    assert unknown.error == "Unknown tool: missing_tool"
    assert timeout.status == "timeout"
    assert "timed out" in timeout.error


def test_nonzero_command_is_a_structured_error(tmp_path):
    result = manager().execute(
        ToolCall(
            "command-failed",
            "run_command",
            {"command": [sys.executable, "-c", "raise SystemExit(3)"]},
        ),
        ToolContext(
            workspace=tmp_path,
            approval=lambda _tool, _arguments: True,
        ),
    )

    assert result.status == "error"
    assert "exit_code=3" in result.error


def test_tool_schemas_are_model_friendly():
    schemas = manager().schemas

    assert {schema["name"] for schema in schemas} >= {
        "calculator",
        "read_file",
        "search_files",
        "apply_patch",
        "run_command",
    }
    assert all(schema["type"] == "function" for schema in schemas)
    assert all(schema["parameters"]["additionalProperties"] is False for schema in schemas)
