from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


FinishReason = Literal["completed", "max_steps", "denied", "error"]
ToolStatus = Literal["success", "error", "denied"]


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class LLMResponse:
    """One normalized model response, never the result of a whole run."""

    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    continuation_items: list[Any] = field(default_factory=list)
    finish_reason: str | None = None


@dataclass(frozen=True)
class ToolResult:
    call_id: str
    name: str
    status: ToolStatus
    output: str = ""
    error: str | None = None


@dataclass(frozen=True)
class Event:
    type: str
    sequence: int
    run_id: str
    step: int
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class RunResult:
    """The accumulated result after Runner reaches a terminal state."""

    content: str
    events: list[Event]
    tool_results: list[ToolResult]
    steps: int
    finish_reason: FinishReason
    run_id: str
