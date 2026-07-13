from dataclasses import dataclass, field


@dataclass
class LLMResponse:
    content: str = ""
    tool_calls: list = field(default_factory=list)


@dataclass
class ToolResult:
    name: str
    status: str
    output: str = ""


@dataclass
class RunResult:
    content: str
    events: list[dict]
    tool_results: list[ToolResult]
    finish_reason: str


result = RunResult(
    content="42",
    events=[{"type": "run_started", "sequence": 1}, {"type": "run_completed", "sequence": 2}],
    tool_results=[ToolResult("calculator", "success", "42")],
    finish_reason="completed",
)
print(f"finish_reason={result.finish_reason} events={len(result.events)}")

