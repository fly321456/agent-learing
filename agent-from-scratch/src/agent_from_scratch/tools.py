from __future__ import annotations

import ast
from dataclasses import dataclass
from datetime import datetime
import operator
from pathlib import Path
import subprocess
import time
from typing import Any, Callable, Literal

from .errors import ToolExecutionError, WorkspaceBoundaryError
from .schemas import ToolCall, ToolResult


ApprovalCallback = Callable[["ToolSpec", dict[str, Any]], bool]
ToolHandler = Callable[..., str]
RiskLevel = Literal["read", "write", "execute"]


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

    def as_schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }


class ToolManager:
    def __init__(self, tools: list[ToolSpec]):
        self._tools = {tool.name: tool for tool in tools}
        if len(self._tools) != len(tools):
            raise ValueError("Tool names must be unique")

    @property
    def schemas(self) -> list[dict[str, Any]]:
        return [tool.as_schema() for tool in self._tools.values()]

    def execute(self, call: ToolCall, context: ToolContext) -> ToolResult:
        tool = self._tools.get(call.name)
        if tool is None:
            return ToolResult(call.id, call.name, "error", error=f"Unknown tool: {call.name}")

        if tool.requires_approval and (
            context.approval is None or not context.approval(tool, call.arguments)
        ):
            return ToolResult(
                call.id,
                call.name,
                "denied",
                error=f"Approval denied for {call.name}",
            )

        started = time.perf_counter()
        try:
            output = tool.handler(context=context, **call.arguments)
            return ToolResult(
                call.id,
                call.name,
                "success",
                output=str(output),
                duration_ms=(time.perf_counter() - started) * 1000,
            )
        except subprocess.TimeoutExpired:
            return ToolResult(
                call.id,
                call.name,
                "timeout",
                error=f"Tool {call.name} timed out after {context.command_timeout:g}s",
                duration_ms=(time.perf_counter() - started) * 1000,
            )
        except Exception as exc:
            return ToolResult(
                call.id,
                call.name,
                "error",
                error=str(exc),
                duration_ms=(time.perf_counter() - started) * 1000,
            )


def _workspace_path(context: ToolContext, path: str) -> Path:
    candidate = (context.workspace / path).resolve()
    try:
        candidate.relative_to(context.workspace)
    except ValueError as exc:
        raise WorkspaceBoundaryError(f"Path is outside the workspace: {path}") from exc
    return candidate


_BINARY_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY_OPERATORS = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def _evaluate_expression(node: ast.AST) -> int | float:
    if isinstance(node, ast.Expression):
        return _evaluate_expression(node.body)
    if isinstance(node, ast.Constant) and type(node.value) in {int, float}:
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPERATORS:
        left = _evaluate_expression(node.left)
        right = _evaluate_expression(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 12:
            raise ValueError("Exponent is too large")
        return _BINARY_OPERATORS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPERATORS:
        return _UNARY_OPERATORS[type(node.op)](_evaluate_expression(node.operand))
    raise ValueError("Expression contains unsupported syntax")


def calculator(*, context: ToolContext, expression: str) -> str:
    del context
    value = _evaluate_expression(ast.parse(expression, mode="eval"))
    return str(value)


def get_current_time(*, context: ToolContext) -> str:
    del context
    return datetime.now().astimezone().isoformat(timespec="seconds")


def read_file(
    *,
    context: ToolContext,
    path: str,
    start_line: int = 1,
    end_line: int | None = None,
    max_chars: int = 20_000,
) -> str:
    if start_line < 1 or (end_line is not None and end_line < start_line):
        raise ValueError("Invalid line range")
    target = _workspace_path(context, path)
    text = target.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    selected = "".join(lines[start_line - 1 : end_line])
    if len(selected) > max_chars:
        return selected[:max_chars] + "\n... [truncated]"
    return selected


def search_files(
    *,
    context: ToolContext,
    query: str,
    path: str = ".",
    glob: str = "*",
    max_results: int = 100,
) -> str:
    root = _workspace_path(context, path)
    matches: list[str] = []
    for file_path in sorted(root.rglob(glob)):
        if not file_path.is_file() or ".git" in file_path.parts:
            continue
        try:
            lines = file_path.read_text(encoding="utf-8").splitlines()
        except (UnicodeDecodeError, OSError):
            continue
        for line_number, line in enumerate(lines, start=1):
            if query in line:
                relative = file_path.relative_to(context.workspace).as_posix()
                matches.append(f"{relative}:{line_number}:{line}")
                if len(matches) >= max_results:
                    return "\n".join(matches) + "\n... [result limit reached]"
    return "\n".join(matches)


def apply_patch(
    *,
    context: ToolContext,
    path: str,
    old_text: str,
    new_text: str,
    replace_all: bool = False,
) -> str:
    target = _workspace_path(context, path)
    text = target.read_text(encoding="utf-8")
    occurrences = text.count(old_text)
    if occurrences == 0:
        raise ValueError("old_text was not found")
    if occurrences > 1 and not replace_all:
        raise ValueError("old_text is not unique; set replace_all=true to replace every match")
    updated = text.replace(old_text, new_text, -1 if replace_all else 1)
    target.write_text(updated, encoding="utf-8", newline="")
    return f"Updated {path}: {occurrences if replace_all else 1} replacement(s)"


def run_command(
    *,
    context: ToolContext,
    command: list[str],
    cwd: str = ".",
) -> str:
    if not command or not all(isinstance(part, str) and part for part in command):
        raise ValueError("command must be a non-empty list of strings")
    working_directory = _workspace_path(context, cwd)
    completed = subprocess.run(
        command,
        cwd=working_directory,
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
        raise ToolExecutionError(output)
    return output


def _object_schema(properties: dict[str, Any], required: list[str]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }


def create_default_tools() -> list[ToolSpec]:
    return [
        ToolSpec(
            "get_current_time",
            "Return the current local date and time.",
            _object_schema({}, []),
            get_current_time,
        ),
        ToolSpec(
            "calculator",
            "Evaluate a basic arithmetic expression without executing code.",
            _object_schema({"expression": {"type": "string"}}, ["expression"]),
            calculator,
        ),
        ToolSpec(
            "read_file",
            "Read UTF-8 text from a file inside the workspace.",
            _object_schema(
                {
                    "path": {"type": "string"},
                    "start_line": {"type": "integer", "minimum": 1},
                    "end_line": {"type": ["integer", "null"], "minimum": 1},
                    "max_chars": {"type": "integer", "minimum": 1},
                },
                ["path"],
            ),
            read_file,
        ),
        ToolSpec(
            "search_files",
            "Search UTF-8 text files inside the workspace.",
            _object_schema(
                {
                    "query": {"type": "string"},
                    "path": {"type": "string"},
                    "glob": {"type": "string"},
                    "max_results": {"type": "integer", "minimum": 1},
                },
                ["query"],
            ),
            search_files,
        ),
        ToolSpec(
            "apply_patch",
            "Replace exact text in one UTF-8 file inside the workspace.",
            _object_schema(
                {
                    "path": {"type": "string"},
                    "old_text": {"type": "string"},
                    "new_text": {"type": "string"},
                    "replace_all": {"type": "boolean"},
                },
                ["path", "old_text", "new_text"],
            ),
            apply_patch,
            risk="write",
        ),
        ToolSpec(
            "run_command",
            "Run an argv-style command in the workspace without a shell.",
            _object_schema(
                {
                    "command": {"type": "array", "items": {"type": "string"}, "minItems": 1},
                    "cwd": {"type": "string"},
                },
                ["command"],
            ),
            run_command,
            risk="execute",
        ),
    ]
