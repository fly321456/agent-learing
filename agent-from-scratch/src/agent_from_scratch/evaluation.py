from dataclasses import dataclass
from importlib.resources import files
import json
from pathlib import Path
import time
from typing import Any

from .agent import Agent
from .llm import FakeLLM
from .runner import Runner
from .schemas import LLMResponse, ToolCall
from .tools import ToolContext, ToolSpec


@dataclass(frozen=True)
class EvalCase:
    id: str
    category: str
    prompt: str
    expected_tools: list[str]


def load_cases(path: Path | None = None) -> list[EvalCase]:
    catalog = path or files("agent_from_scratch").joinpath("data", "cases.json")
    data = json.loads(catalog.read_text(encoding="utf-8"))
    return [EvalCase(**item) for item in data]


def summarize_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    failures: dict[str, int] = {}
    for result in results:
        failure = result.get("failure")
        if failure:
            failures[failure] = failures.get(failure, 0) + 1
    passed = sum(bool(result["passed"]) for result in results)
    total = len(results)
    return {
        "total": total,
        "passed": passed,
        "success_rate": passed / total if total else 0.0,
        "tool_calls": sum(int(result["tool_calls"]) for result in results),
        "steps": sum(int(result["steps"]) for result in results),
        "duration_ms": sum(float(result["duration_ms"]) for result in results),
        "failures": failures,
    }


def run_offline_protocol_eval(cases: list[EvalCase]) -> dict[str, Any]:
    """Exercise recorded tool sequences without executing real tools or using a model."""

    tool_names = sorted({name for case in cases for name in case.expected_tools})

    def stub_tool(*, context: ToolContext) -> str:
        del context
        return "ok"

    tools = [
        ToolSpec(
            name=name,
            description=f"Offline protocol stub for {name}.",
            parameters={
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
            handler=stub_tool,
        )
        for name in tool_names
    ]
    results: list[dict[str, Any]] = []
    for case in cases:
        calls = [
            ToolCall(id=f"{case.id}-{index}", name=name, arguments={})
            for index, name in enumerate(case.expected_tools, start=1)
        ]
        llm = FakeLLM(
            [
                LLMResponse(tool_calls=calls, finish_reason="tool_calls"),
                LLMResponse(content="offline protocol complete", finish_reason="completed"),
            ]
        )
        agent = Agent("offline-eval", "Follow the scripted protocol.", llm, tools, max_steps=2)
        started = time.perf_counter()
        result = Runner().run(agent, case.prompt, context=ToolContext(workspace=Path.cwd()))
        actual_tools = [tool_result.name for tool_result in result.tool_results]
        passed = result.finish_reason == "completed" and actual_tools == case.expected_tools
        failure = None
        if result.finish_reason != "completed":
            failure = result.finish_reason
        elif actual_tools != case.expected_tools:
            failure = "tool_sequence"
        results.append(
            {
                "passed": passed,
                "tool_calls": len(result.tool_results),
                "steps": result.steps,
                "duration_ms": (time.perf_counter() - started) * 1000,
                "failure": failure,
            }
        )
    return summarize_results(results)


def main() -> None:
    cases = load_cases()
    print(
        json.dumps(
            {
                "valid_cases": len(cases),
                "mode": "offline_protocol",
                "summary": run_offline_protocol_eval(cases),
            },
            ensure_ascii=False,
        )
    )
