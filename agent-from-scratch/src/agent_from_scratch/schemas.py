from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal


FinishReason = Literal["completed", "tool_calls", "max_steps", "denied", "error"]
ToolStatus = Literal["success", "error", "denied", "timeout"]


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
    duration_ms: float = 0.0


@dataclass(frozen=True)
class Event:
    type: str
    sequence: int
    run_id: str
    step: int
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class LLMResponse:
    """Normalized result of one model call, not of the whole agent run."""

    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    continuation_items: list[Any] = field(default_factory=list)
    finish_reason: FinishReason | None = None
    raw_response: Any | None = field(default=None, repr=False, compare=False)


@dataclass
class RunResult:
    """Stable result returned after the runner reaches a terminal state."""

    content: str
    events: list[Event]
    tool_results: list[ToolResult]
    steps: int
    finish_reason: FinishReason
    run_id: str

