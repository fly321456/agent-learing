from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: Any


@dataclass
class ModelResponse:
    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)


class ScriptedModel:
    def __init__(self, responses: Iterable[ModelResponse], repeat_last: bool = False):
        self.responses = list(responses)
        self.repeat_last = repeat_last
        self.index = 0
        self.requests: list[list[dict[str, Any]]] = []

    def generate(self, items: list[dict[str, Any]], tools: list[str]) -> ModelResponse:
        del tools
        self.requests.append(list(items))
        if self.index >= len(self.responses):
            if self.repeat_last and self.responses:
                return self.responses[-1]
            raise RuntimeError("ScriptedModel has no response left")
        response = self.responses[self.index]
        self.index += 1
        return response


def execute_tool(call: ToolCall, tools: dict[str, Callable[..., Any]]) -> dict[str, Any]:
    if not isinstance(call.arguments, dict):
        return {"call_id": call.id, "name": call.name, "status": "invalid_arguments"}
    handler = tools.get(call.name)
    if handler is None:
        return {"call_id": call.id, "name": call.name, "status": "unknown_tool"}
    try:
        output = handler(**call.arguments)
        return {"call_id": call.id, "name": call.name, "status": "success", "output": str(output)}
    except Exception as error:
        return {"call_id": call.id, "name": call.name, "status": "error", "error": str(error)}


def run_agent(task: str, model: ScriptedModel, tools: dict[str, Callable[..., Any]], max_steps: int = 5):
    if max_steps < 1:
        raise ValueError("max_steps must be positive")
    items: list[dict[str, Any]] = [{"role": "user", "content": task}]
    results: list[dict[str, Any]] = []
    trace: list[dict[str, Any]] = []
    for step in range(1, max_steps + 1):
        response = model.generate(items, list(tools))
        trace.append({"step": step, "tool_calls": len(response.tool_calls), "content": response.content})
        if not response.tool_calls:
            return {"answer": response.content, "tool_results": results, "trace": trace,
                    "steps": step, "finish_reason": "completed"}
        for call in response.tool_calls:
            result = execute_tool(call, tools)
            results.append(result)
            items.append({"type": "function_call", "call_id": call.id,
                          "name": call.name, "arguments": call.arguments})
            items.append({"type": "function_call_output", "call_id": call.id,
                          "output": result})
    return {"answer": "", "tool_results": results, "trace": trace,
            "steps": max_steps, "finish_reason": "max_steps"}

