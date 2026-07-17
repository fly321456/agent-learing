from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import pytest

from agent_from_scratch.cli import _approve
from agent_from_scratch.schemas import Event, ToolCall
from agent_from_scratch.session import (
    CheckpointStore,
    RunCheckpoint,
    Session,
    SessionStore,
)
from agent_from_scratch.tools import ToolContext, ToolManager, ToolSpec, create_default_tools
from agent_from_scratch.tracing import JsonlTraceWriter


SECRET_SENTINEL = "sk-test-secret-sentinel-never-log"


def _manager() -> ToolManager:
    return ToolManager(create_default_tools())


def _checkpoint(run_id: str) -> RunCheckpoint:
    return RunCheckpoint(
        run_id=run_id,
        user_input="test",
        input_items=[],
        events=[],
        tool_results=[],
        next_step=1,
    )


def _create_directory_link(link: Path, target: Path) -> None:
    if os.name == "nt":
        completed = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(target)],
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            pytest.skip(f"Windows junction creation is unavailable: {completed.stderr}")
        return

    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"Directory symlink creation is unavailable: {exc}")


def test_search_files_rejects_parent_directory_glob(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text(f"needle {SECRET_SENTINEL}\n", encoding="utf-8")

    result = _manager().execute(
        ToolCall(
            "search-parent",
            "search_files",
            {"query": "needle", "path": ".", "glob": "../outside.txt"},
        ),
        ToolContext(workspace=workspace),
    )

    assert result.status == "error"
    assert SECRET_SENTINEL not in (result.output + (result.error or ""))


def test_search_files_does_not_follow_workspace_link_outside_boundary(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.txt").write_text(
        f"needle {SECRET_SENTINEL}\n",
        encoding="utf-8",
    )
    _create_directory_link(workspace / "linked", outside)

    result = _manager().execute(
        ToolCall(
            "search-link",
            "search_files",
            {"query": "needle", "path": ".", "glob": "*.txt"},
        ),
        ToolContext(workspace=workspace),
    )

    payload = result.output + (result.error or "")
    assert SECRET_SENTINEL not in payload
    assert "linked/secret.txt" not in result.output.replace("\\", "/")


@pytest.mark.parametrize("operation", ["save", "load"])
@pytest.mark.parametrize(
    "invalid_id",
    ["../escape", "..\\escape", "nested/session", "nested\\session"],
)
def test_session_store_rejects_ids_with_parent_or_path_separators(
    tmp_path,
    operation,
    invalid_id,
):
    store = SessionStore(tmp_path / "sessions")

    with pytest.raises(ValueError):
        if operation == "save":
            store.save(Session(invalid_id))
        else:
            store.load(invalid_id)


@pytest.mark.parametrize("operation", ["save", "load"])
def test_session_store_rejects_absolute_ids(tmp_path, operation):
    store = SessionStore(tmp_path / "sessions")
    invalid_id = str((tmp_path / "absolute-session").resolve())

    with pytest.raises(ValueError):
        if operation == "save":
            store.save(Session(invalid_id))
        else:
            store.load(invalid_id)


@pytest.mark.parametrize("operation", ["save", "load"])
@pytest.mark.parametrize(
    "invalid_id",
    ["../escape", "..\\escape", "nested/checkpoint", "nested\\checkpoint"],
)
def test_checkpoint_store_rejects_ids_with_parent_or_path_separators(
    tmp_path,
    operation,
    invalid_id,
):
    store = CheckpointStore(tmp_path / "checkpoints")

    with pytest.raises(ValueError):
        if operation == "save":
            store.save(_checkpoint(invalid_id))
        else:
            store.load(invalid_id)


@pytest.mark.parametrize("operation", ["save", "load"])
def test_checkpoint_store_rejects_absolute_ids(tmp_path, operation):
    store = CheckpointStore(tmp_path / "checkpoints")
    invalid_id = str((tmp_path / "absolute-checkpoint").resolve())

    with pytest.raises(ValueError):
        if operation == "save":
            store.save(_checkpoint(invalid_id))
        else:
            store.load(invalid_id)


def test_read_file_enforces_server_cap_even_when_model_requests_more(tmp_path):
    (tmp_path / "large.txt").write_text("x" * 30_000, encoding="utf-8")

    result = _manager().execute(
        ToolCall(
            "read-large",
            "read_file",
            {"path": "large.txt", "max_chars": 1_000_000},
        ),
        ToolContext(workspace=tmp_path),
    )

    assert result.status == "success"
    assert len(result.output) < 30_000
    assert "truncated" in result.output.lower()


def test_search_files_enforces_server_cap_even_when_model_requests_more(tmp_path):
    (tmp_path / "many.txt").write_text(
        "".join(f"needle {index}\n" for index in range(250)),
        encoding="utf-8",
    )

    result = _manager().execute(
        ToolCall(
            "search-many",
            "search_files",
            {"query": "needle", "max_results": 1_000_000},
        ),
        ToolContext(workspace=tmp_path),
    )

    assert result.status == "success"
    assert result.output.count("needle") < 250
    assert "result limit reached" in result.output.lower()


@pytest.mark.parametrize(
    "call",
    [
        ToolCall("read-zero", "read_file", {"path": "data.txt", "max_chars": 0}),
        ToolCall(
            "search-zero",
            "search_files",
            {"query": "needle", "max_results": 0},
        ),
    ],
)
def test_tool_limits_reject_non_positive_values_at_runtime(tmp_path, call):
    (tmp_path / "data.txt").write_text("needle\n", encoding="utf-8")

    result = _manager().execute(call, ToolContext(workspace=tmp_path))

    assert result.status == "error"


def test_run_command_output_is_bounded(tmp_path):
    result = _manager().execute(
        ToolCall(
            "command-large-output",
            "run_command",
            {
                "command": [
                    sys.executable,
                    "-c",
                    (
                        "import sys; "
                        "print('A' * 100_000); "
                        "print('B' * 100_000, file=sys.stderr)"
                    ),
                ]
            },
        ),
        ToolContext(
            workspace=tmp_path,
            approval=lambda _tool, _arguments: True,
        ),
    )

    assert result.status == "success"
    assert len(result.output) < 200_000
    assert "truncated" in result.output.lower()


def test_custom_tool_output_is_bounded_by_manager(tmp_path):
    tool = ToolSpec(
        name="large_observation",
        description="Return an intentionally large observation.",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
        handler=lambda *, context: "x" * 100_000,
        risk="read",
    )

    result = ToolManager([tool]).execute(
        ToolCall("large-observation", "large_observation", {}),
        ToolContext(workspace=tmp_path),
    )

    assert result.status == "success"
    assert len(result.output) <= 20_000
    assert "truncated" in result.output.lower()


def test_malformed_tool_schema_returns_error_instead_of_escaping_manager(tmp_path):
    tool = ToolSpec(
        name="malformed",
        description="Contains a required field with no property schema.",
        parameters={
            "type": "object",
            "properties": {},
            "required": ["missing"],
            "additionalProperties": False,
        },
        handler=lambda *, context: "must not run",
        risk="read",
    )

    result = ToolManager([tool]).execute(
        ToolCall("malformed-schema", "malformed", {}),
        ToolContext(workspace=tmp_path),
    )

    assert result.status == "error"
    assert "schema" in result.error.lower()


def test_trace_writer_redacts_secrets_and_truncates_large_values(tmp_path):
    trace_path = tmp_path / "trace.jsonl"
    writer = JsonlTraceWriter(trace_path)
    event = Event(
        type="tool_called",
        sequence=1,
        run_id="run-1",
        step=1,
        data={
            "arguments": {
                "api_key": SECRET_SENTINEL,
                "new_text": "x" * 50_000,
            }
        },
    )

    writer(event)

    persisted = trace_path.read_text(encoding="utf-8")
    assert SECRET_SENTINEL not in persisted
    assert len(persisted) < 50_000
    assert "redact" in persisted.lower()
    assert "truncat" in persisted.lower()


def test_cli_approval_redacts_secrets_and_truncates_large_values(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr("builtins.input", lambda _prompt: "n")
    tool = next(tool for tool in create_default_tools() if tool.name == "apply_patch")

    approved = _approve(
        tool,
        {
            "path": "demo.txt",
            "api_key": SECRET_SENTINEL,
            "new_text": "x" * 10_000,
        },
    )

    captured = capsys.readouterr()
    assert approved is False
    assert SECRET_SENTINEL not in captured.err
    assert len(captured.err) < 10_000
    assert "redact" in captured.err.lower()
    assert "truncat" in captured.err.lower()


def test_cli_eof_denies_risky_tool_without_running_handler(monkeypatch, tmp_path):
    executed = False

    def handler(*, context: ToolContext) -> str:
        del context
        nonlocal executed
        executed = True
        return "executed"

    monkeypatch.setattr(
        "builtins.input",
        lambda _prompt: (_ for _ in ()).throw(EOFError()),
    )
    tool = ToolSpec(
        name="risky",
        description="A risky test tool.",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
        handler=handler,
        risk="write",
    )

    result = ToolManager([tool]).execute(
        ToolCall("risky-1", "risky", {}),
        ToolContext(workspace=tmp_path, approval=_approve),
    )

    assert result.status == "denied"
    assert executed is False


def test_apply_patch_preserves_crlf_bytes(tmp_path):
    target = tmp_path / "windows.txt"
    target.write_bytes(b"first\r\nsecond\r\n")
    manager = _manager()

    result = manager.execute(
        ToolCall(
            "patch-crlf",
            "apply_patch",
            {
                "path": "windows.txt",
                "old_text": "second",
                "new_text": "updated",
            },
        ),
        ToolContext(
            workspace=tmp_path,
            approval=lambda _tool, _arguments: True,
        ),
    )

    assert result.status == "success"
    assert target.read_bytes() == b"first\r\nupdated\r\n"


def test_apply_patch_rejects_empty_old_text(tmp_path):
    target = tmp_path / "data.txt"
    target.write_text("unchanged", encoding="utf-8")

    result = _manager().execute(
        ToolCall(
            "patch-empty",
            "apply_patch",
            {
                "path": "data.txt",
                "old_text": "",
                "new_text": "unexpected",
            },
        ),
        ToolContext(
            workspace=tmp_path,
            approval=lambda _tool, _arguments: True,
        ),
    )

    assert result.status == "error"
    assert target.read_text(encoding="utf-8") == "unchanged"


def test_tool_without_explicit_risk_fails_closed(tmp_path):
    executed = False

    def handler(*, context: ToolContext) -> str:
        del context
        nonlocal executed
        executed = True
        return "executed"

    tool = ToolSpec(
        name="unclassified",
        description="A tool whose author omitted the risk classification.",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
        handler=handler,
    )

    result = ToolManager([tool]).execute(
        ToolCall("unclassified-1", "unclassified", {}),
        ToolContext(workspace=tmp_path),
    )

    assert result.status == "denied"
    assert executed is False


def test_session_store_rejects_future_schema_version(tmp_path):
    directory = tmp_path / "sessions"
    directory.mkdir()
    (directory / "future.json").write_text(
        '{"schema_version": 999, "id": "future", "messages": []}',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="schema version"):
        SessionStore(directory).load("future")


def test_session_store_rejects_oversized_state_file(tmp_path):
    directory = tmp_path / "sessions"
    directory.mkdir()
    (directory / "large.json").write_bytes(b" " * 5_000_001)

    with pytest.raises(ValueError, match="too large"):
        SessionStore(directory).load("large")
