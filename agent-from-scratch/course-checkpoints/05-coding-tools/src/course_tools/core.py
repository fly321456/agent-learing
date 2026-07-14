from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
import time
from typing import Any, Callable, Literal


class WorkspaceBoundaryError(ValueError):
    pass


class CommandFailed(RuntimeError):
    def __init__(self, output: str, exit_code: int):
        super().__init__(f"Command failed with exit code {exit_code}")
        self.output = output
        self.exit_code = exit_code


RiskLevel = Literal["read", "write", "execute"]
ToolStatus = Literal["success", "error", "denied", "timeout"]
ApprovalCallback = Callable[["ToolSpec", dict[str, Any]], bool]
ToolHandler = Callable[..., str]


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class ToolResult:
    call_id: str
    name: str
    status: ToolStatus
    output: str = ""
    error: str | None = None
    exit_code: int | None = None
    duration_ms: float = 0.0


@dataclass(frozen=True)
class ToolContext:
    workspace: Path
    approval: ApprovalCallback | None = None
    command_timeout: float = 30.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "workspace", Path(self.workspace).resolve())
        if self.command_timeout <= 0:
            raise ValueError("command_timeout must be positive")


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]
    handler: ToolHandler
    risk: RiskLevel = "read"

    @property
    def requires_approval(self) -> bool:
        return self.risk in {"write", "execute"}


class ToolManager:
    def __init__(self, tools: list[ToolSpec]):
        self._tools = {tool.name: tool for tool in tools}
        if len(self._tools) != len(tools):
            raise ValueError("Tool names must be unique")

    def execute(self, call: ToolCall, context: ToolContext) -> ToolResult:
        tool = self._tools.get(call.name)
        if tool is None:
            return ToolResult(call.id, call.name, "error", error=f"Unknown tool: {call.name}")
        if tool.requires_approval and (
            context.approval is None or not context.approval(tool, call.arguments)
        ):
            return ToolResult(call.id, call.name, "denied", error=f"Approval denied for {call.name}")

        started = time.perf_counter()
        try:
            output = tool.handler(context=context, **call.arguments)
            return ToolResult(
                call.id, call.name, "success", output=str(output),
                duration_ms=(time.perf_counter() - started) * 1000,
            )
        except subprocess.TimeoutExpired:
            return ToolResult(
                call.id, call.name, "timeout",
                error=f"Tool {call.name} timed out after {context.command_timeout:g}s",
                duration_ms=(time.perf_counter() - started) * 1000,
            )
        except CommandFailed as exc:
            return ToolResult(
                call.id, call.name, "error", output=exc.output, error=str(exc),
                exit_code=exc.exit_code,
                duration_ms=(time.perf_counter() - started) * 1000,
            )
        except Exception as exc:
            return ToolResult(
                call.id, call.name, "error", error=str(exc),
                duration_ms=(time.perf_counter() - started) * 1000,
            )


def workspace_path(context: ToolContext, path: str) -> Path:
    target = (context.workspace / path).resolve()
    try:
        target.relative_to(context.workspace)
    except ValueError as exc:
        raise WorkspaceBoundaryError(f"Path is outside the workspace: {path}") from exc
    return target


def read_file(
    *, context: ToolContext, path: str, start_line: int = 1,
    end_line: int | None = None, max_chars: int = 20_000,
) -> str:
    if start_line < 1 or (end_line is not None and end_line < start_line):
        raise ValueError("Invalid line range")
    if max_chars < 1:
        raise ValueError("max_chars must be positive")
    text = workspace_path(context, path).read_text(encoding="utf-8", errors="strict")
    selected = "".join(text.splitlines(keepends=True)[start_line - 1:end_line])
    if len(selected) > max_chars:
        return selected[:max_chars] + "\n... [truncated]"
    return selected


def search_files(
    *, context: ToolContext, query: str, path: str = ".", glob: str = "*",
    max_results: int = 100,
) -> str:
    if max_results < 1:
        raise ValueError("max_results must be positive")
    root = workspace_path(context, path)
    matches: list[str] = []
    for candidate in sorted(root.rglob(glob)):
        if not candidate.is_file() or ".git" in candidate.parts:
            continue
        try:
            lines = candidate.read_text(encoding="utf-8", errors="strict").splitlines()
        except (UnicodeDecodeError, OSError):
            continue
        for line_number, line in enumerate(lines, start=1):
            if query not in line:
                continue
            relative = candidate.relative_to(context.workspace).as_posix()
            matches.append(f"{relative}:{line_number}:{line}")
            if len(matches) >= max_results:
                return "\n".join(matches) + "\n... [result limit reached]"
    return "\n".join(matches)


def apply_patch(
    *, context: ToolContext, path: str, old_text: str, new_text: str,
) -> str:
    target = workspace_path(context, path)
    text = target.read_text(encoding="utf-8", errors="strict")
    occurrences = text.count(old_text)
    if occurrences == 0:
        raise ValueError("old_text was not found")
    if occurrences != 1:
        raise ValueError("old_text is not unique")
    target.write_text(text.replace(old_text, new_text, 1), encoding="utf-8", newline="")
    return f"Updated {path}: 1 replacement"


def run_command(
    *, context: ToolContext, command: list[str], cwd: str = ".",
) -> str:
    if not command or not all(isinstance(part, str) and part for part in command):
        raise ValueError("command must be a non-empty argv list")
    completed = subprocess.run(
        command,
        cwd=workspace_path(context, cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=context.command_timeout,
        check=False,
        shell=False,
    )
    output = (
        f"exit_code={completed.returncode}\n"
        f"stdout:\n{completed.stdout}\n"
        f"stderr:\n{completed.stderr}"
    )
    if completed.returncode != 0:
        raise CommandFailed(output, completed.returncode)
    return output


def create_coding_tools() -> list[ToolSpec]:
    empty_schema = {"type": "object"}
    return [
        ToolSpec("read_file", "Read UTF-8 text inside the workspace.", empty_schema, read_file),
        ToolSpec("search_files", "Search text with a result limit.", empty_schema, search_files),
        ToolSpec("apply_patch", "Replace one exact unique text span.", empty_schema, apply_patch, "write"),
        ToolSpec("run_command", "Run an argv command without a shell.", empty_schema, run_command, "execute"),
    ]
