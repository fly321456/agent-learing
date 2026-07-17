from __future__ import annotations

import ast
from dataclasses import dataclass
from datetime import datetime
import os
import operator
from pathlib import Path
import subprocess
import tempfile
import threading
import time
from typing import Any, Callable, IO, Literal

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
    max_read_chars: int = 20_000
    max_search_results: int = 100
    max_search_line_chars: int = 1_000
    max_search_file_bytes: int = 1_000_000
    max_search_candidates: int = 10_000
    max_tool_output_chars: int = 20_000
    max_command_output_chars: int = 20_000

    def __post_init__(self) -> None:
        object.__setattr__(self, "workspace", Path(self.workspace).resolve())
        if self.command_timeout <= 0:
            raise ValueError("command_timeout must be positive")
        for field_name in (
            "max_read_chars",
            "max_search_results",
            "max_search_line_chars",
            "max_search_file_bytes",
            "max_search_candidates",
            "max_tool_output_chars",
            "max_command_output_chars",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                raise ValueError(f"{field_name} must be a positive integer")


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]
    handler: ToolHandler
    risk: RiskLevel = "execute"

    @property
    def requires_approval(self) -> bool:
        return self.risk in {"write", "execute"}

    def as_schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "strict": True,
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

        try:
            arguments = _validated_arguments(tool.parameters, call.arguments)
        except (TypeError, ValueError) as exc:
            return ToolResult(
                call.id,
                call.name,
                "error",
                error=f"Invalid arguments for {call.name}: {exc}",
            )

        if tool.requires_approval:
            try:
                approved = context.approval is not None and context.approval(
                    tool, arguments
                )
            except Exception:
                approved = False
            if not approved:
                return ToolResult(
                    call.id,
                    call.name,
                    "denied",
                    error=f"Approval denied for {call.name}",
                )

        started = time.perf_counter()
        try:
            output = tool.handler(context=context, **arguments)
            return ToolResult(
                call.id,
                call.name,
                "success",
                output=_truncate_text(str(output), context.max_tool_output_chars),
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


def _schema_types(schema: dict[str, Any]) -> list[str]:
    value = schema.get("type")
    return value if isinstance(value, list) else [value]


def _validate_schema_value(value: Any, schema: dict[str, Any], path: str) -> None:
    schema_types = _schema_types(schema)
    valid = (
        (value is None and "null" in schema_types)
        or (isinstance(value, str) and "string" in schema_types)
        or (
            isinstance(value, int)
            and not isinstance(value, bool)
            and "integer" in schema_types
        )
        or (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and "number" in schema_types
        )
        or (isinstance(value, bool) and "boolean" in schema_types)
        or (isinstance(value, list) and "array" in schema_types)
        or (isinstance(value, dict) and "object" in schema_types)
    )
    if not valid:
        raise TypeError(f"{path} does not match type {schema.get('type')!r}")
    if value is None:
        return
    if "minimum" in schema and value < schema["minimum"]:
        raise ValueError(f"{path} is below the minimum")
    if "maximum" in schema and value > schema["maximum"]:
        raise ValueError(f"{path} exceeds the maximum")
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            raise ValueError(f"{path} has too few items")
        for index, item in enumerate(value):
            _validate_schema_value(item, schema.get("items", {}), f"{path}[{index}]")
    if isinstance(value, dict):
        _validated_arguments(schema, value, path=path)


def _validated_arguments(
    schema: dict[str, Any], arguments: Any, *, path: str = "arguments"
) -> dict[str, Any]:
    if not isinstance(arguments, dict):
        raise TypeError(f"{path} must be an object")
    properties = schema.get("properties", {})
    if not isinstance(properties, dict):
        raise TypeError(f"{path} schema properties must be an object")
    extras = set(arguments) - set(properties)
    if extras and schema.get("additionalProperties") is False:
        raise ValueError(f"{path} contains unknown fields: {sorted(extras)}")
    normalized = dict(arguments)
    for name in schema.get("required", []):
        if name not in properties:
            raise ValueError(f"{path} schema requires unknown property {name!r}")
        if name not in normalized:
            if "null" in _schema_types(properties[name]):
                normalized[name] = None
            else:
                raise ValueError(f"{path}.{name} is required")
    for name, value in normalized.items():
        child_schema = properties.get(name)
        if child_schema is not None:
            _validate_schema_value(value, child_schema, f"{path}.{name}")
    return normalized


def _bounded_positive_integer(value: int, hard_cap: int, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ValueError(f"{name} must be a positive integer")
    return min(value, hard_cap)


def _truncate_text(value: str, max_chars: int) -> str:
    marker = "\n... [truncated]"
    if len(value) <= max_chars:
        return value
    kept = max(0, max_chars - len(marker))
    return value[:kept] + marker


def _validate_search_glob(glob: str) -> None:
    if not isinstance(glob, str) or not glob:
        raise ValueError("glob must be a non-empty relative pattern")
    normalized = glob.replace("\\", "/")
    if Path(glob).is_absolute() or any(part == ".." for part in normalized.split("/")):
        raise WorkspaceBoundaryError("glob must stay inside the search root")


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
    start_line: int | None = 1,
    end_line: int | None = None,
    max_chars: int | None = 20_000,
) -> str:
    start_line = 1 if start_line is None else start_line
    max_chars = context.max_read_chars if max_chars is None else max_chars
    if start_line < 1 or (end_line is not None and end_line < start_line):
        raise ValueError("Invalid line range")
    effective_max_chars = _bounded_positive_integer(
        max_chars, context.max_read_chars, "max_chars"
    )
    target = _workspace_path(context, path)
    text = target.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    selected = "".join(lines[start_line - 1 : end_line])
    return _truncate_text(selected, effective_max_chars)


def search_files(
    *,
    context: ToolContext,
    query: str,
    path: str | None = ".",
    glob: str | None = "*",
    max_results: int | None = 100,
) -> str:
    path = "." if path is None else path
    glob = "*" if glob is None else glob
    max_results = context.max_search_results if max_results is None else max_results
    _validate_search_glob(glob)
    effective_max_results = _bounded_positive_integer(
        max_results, context.max_search_results, "max_results"
    )
    root = _workspace_path(context, path)
    matches: list[str] = []
    candidates_seen = 0
    for file_path in root.rglob(glob):
        candidates_seen += 1
        if candidates_seen > context.max_search_candidates:
            break
        try:
            resolved = file_path.resolve()
            relative = resolved.relative_to(context.workspace)
        except (OSError, ValueError):
            continue
        if not resolved.is_file() or ".git" in relative.parts:
            continue
        try:
            if resolved.stat().st_size > context.max_search_file_bytes:
                continue
            lines = resolved.read_text(encoding="utf-8").splitlines()
        except (UnicodeDecodeError, OSError):
            continue
        for line_number, line in enumerate(lines, start=1):
            if query in line:
                line = _truncate_text(line, context.max_search_line_chars)
                matches.append(f"{relative.as_posix()}:{line_number}:{line}")
                if len(matches) >= effective_max_results:
                    return "\n".join(matches) + "\n... [result limit reached]"
    output = "\n".join(matches)
    if candidates_seen > context.max_search_candidates:
        output += "\n... [candidate limit reached]"
    return output


def apply_patch(
    *,
    context: ToolContext,
    path: str,
    old_text: str,
    new_text: str,
    replace_all: bool | None = False,
) -> str:
    replace_all = False if replace_all is None else replace_all
    if old_text == "":
        raise ValueError("old_text must not be empty")
    target = _workspace_path(context, path)
    with target.open("r", encoding="utf-8", newline="") as source:
        text = source.read()
    occurrences = text.count(old_text)
    if occurrences == 0:
        raise ValueError("old_text was not found")
    if occurrences > 1 and not replace_all:
        raise ValueError("old_text is not unique; set replace_all=true to replace every match")
    updated = text.replace(old_text, new_text, -1 if replace_all else 1)
    original_mode = target.stat().st_mode
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            newline="",
            dir=target.parent,
            prefix=f".{target.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary.write(updated)
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_name = temporary.name
        os.chmod(temporary_name, original_mode)
        os.replace(temporary_name, target)
    finally:
        if temporary_name is not None:
            try:
                Path(temporary_name).unlink(missing_ok=True)
            except OSError:
                pass
    return f"Updated {path}: {occurrences if replace_all else 1} replacement(s)"


def run_command(
    *,
    context: ToolContext,
    command: list[str],
    cwd: str | None = ".",
) -> str:
    cwd = "." if cwd is None else cwd
    if not command or not all(isinstance(part, str) and part for part in command):
        raise ValueError("command must be a non-empty list of strings")
    working_directory = _workspace_path(context, cwd)
    process = subprocess.Popen(
        command,
        cwd=working_directory,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        shell=False,
    )
    captured: dict[str, list[str]] = {"stdout": [], "stderr": []}
    truncated: dict[str, bool] = {"stdout": False, "stderr": False}

    def drain(name: str, stream: IO[str]) -> None:
        retained = 0
        try:
            while chunk := stream.read(4096):
                remaining = context.max_command_output_chars - retained
                if remaining > 0:
                    captured[name].append(chunk[:remaining])
                    retained += min(len(chunk), remaining)
                if len(chunk) > remaining:
                    truncated[name] = True
        finally:
            stream.close()

    assert process.stdout is not None and process.stderr is not None
    readers = [
        threading.Thread(target=drain, args=("stdout", process.stdout), daemon=True),
        threading.Thread(target=drain, args=("stderr", process.stderr), daemon=True),
    ]
    for reader in readers:
        reader.start()
    try:
        return_code = process.wait(timeout=context.command_timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
        for reader in readers:
            reader.join()
        raise
    for reader in readers:
        reader.join()

    stdout = "".join(captured["stdout"])
    stderr = "".join(captured["stderr"])
    if truncated["stdout"]:
        stdout += "\n... [stdout truncated]"
    if truncated["stderr"]:
        stderr += "\n... [stderr truncated]"
    output = (
        f"exit_code={return_code}\n"
        f"stdout:\n{stdout}\n"
        f"stderr:\n{stderr}"
    )
    output = _truncate_text(output, context.max_command_output_chars)
    if return_code != 0:
        raise ToolExecutionError(output)
    return output


def _object_schema(properties: dict[str, Any], required: list[str]) -> dict[str, Any]:
    del required
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
    }


def create_default_tools() -> list[ToolSpec]:
    return [
        ToolSpec(
            "get_current_time",
            "Return the current local date and time.",
            _object_schema({}, []),
            get_current_time,
            risk="read",
        ),
        ToolSpec(
            "calculator",
            "Evaluate a basic arithmetic expression without executing code.",
            _object_schema({"expression": {"type": "string"}}, ["expression"]),
            calculator,
            risk="read",
        ),
        ToolSpec(
            "read_file",
            "Read UTF-8 text from a file inside the workspace.",
            _object_schema(
                {
                    "path": {"type": "string"},
                    "start_line": {"type": ["integer", "null"], "minimum": 1},
                    "end_line": {"type": ["integer", "null"], "minimum": 1},
                    "max_chars": {"type": ["integer", "null"], "minimum": 1},
                },
                ["path"],
            ),
            read_file,
            risk="read",
        ),
        ToolSpec(
            "search_files",
            "Search UTF-8 text files inside the workspace.",
            _object_schema(
                {
                    "query": {"type": "string"},
                    "path": {"type": ["string", "null"]},
                    "glob": {"type": ["string", "null"]},
                    "max_results": {"type": ["integer", "null"], "minimum": 1},
                },
                ["query"],
            ),
            search_files,
            risk="read",
        ),
        ToolSpec(
            "apply_patch",
            "Replace exact text in one UTF-8 file inside the workspace.",
            _object_schema(
                {
                    "path": {"type": "string"},
                    "old_text": {"type": "string"},
                    "new_text": {"type": "string"},
                    "replace_all": {"type": ["boolean", "null"]},
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
                    "cwd": {"type": ["string", "null"]},
                },
                ["command"],
            ),
            run_command,
            risk="execute",
        ),
    ]
