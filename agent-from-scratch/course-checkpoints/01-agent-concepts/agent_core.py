from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any


Decision = dict[str, Any]
Observation = dict[str, Any]
Tool = Callable[..., Any]
TOOLS: dict[str, Tool] = {}


class ScriptedLLM:
    """Return predetermined decisions so the first module stays fully offline."""

    def __init__(self, decisions: Iterable[Decision]) -> None:
        self._decisions = list(decisions)
        self._position = 0
        self.seen_observations: list[list[Observation]] = []

    def decide(self, task: str, observations: list[Observation]) -> Decision:
        del task
        self.seen_observations.append([item.copy() for item in observations])
        if self._position >= len(self._decisions):
            raise RuntimeError("ScriptedLLM has no decision left")

        decision = self._decisions[self._position]
        self._position += 1
        return decision.copy()


def run_agent(
    task: str,
    llm: ScriptedLLM,
    tools: dict[str, Tool] | None = None,
    max_steps: int = 5,
) -> dict[str, Any]:
    """Run the smallest useful Decide-Act-Observe teaching loop."""
    if max_steps < 1:
        raise ValueError("max_steps must be at least 1")

    available_tools = TOOLS if tools is None else tools
    observations: list[Observation] = []
    trace: list[dict[str, Any]] = []

    for step in range(1, max_steps + 1):
        try:
            decision = llm.decide(task, observations)
        except Exception as error:
            trace.append(
                {
                    "step": step,
                    "decision": None,
                    "observation": {"status": "decision_error", "error": str(error)},
                }
            )
            return {"answer": None, "trace": trace, "finish_reason": "decision_error"}

        entry: dict[str, Any] = {"step": step, "decision": decision}
        decision_type = decision.get("type")

        if decision_type == "finish":
            answer = str(decision.get("answer", ""))
            entry["finish"] = answer
            trace.append(entry)
            return {"answer": answer, "trace": trace, "finish_reason": "completed"}

        if decision_type != "tool":
            entry["observation"] = {
                "status": "invalid_decision",
                "error": "decision type must be 'tool' or 'finish'",
            }
            trace.append(entry)
            return {"answer": None, "trace": trace, "finish_reason": "invalid_decision"}

        tool_name = str(decision.get("name", ""))
        arguments = decision.get("arguments", {})
        if not isinstance(arguments, dict):
            entry["observation"] = {
                "status": "invalid_arguments",
                "tool": tool_name,
                "error": "tool arguments must be a dictionary",
            }
            trace.append(entry)
            return {"answer": None, "trace": trace, "finish_reason": "invalid_arguments"}

        entry["action"] = {"tool": tool_name, "arguments": arguments.copy()}
        tool = available_tools.get(tool_name)
        if tool is None:
            observation = {
                "status": "unknown_tool",
                "tool": tool_name,
                "error": f"tool is not registered: {tool_name}",
            }
            entry["observation"] = observation
            trace.append(entry)
            return {"answer": None, "trace": trace, "finish_reason": "unknown_tool"}

        try:
            output = tool(**arguments)
            observation = {"status": "success", "tool": tool_name, "output": output}
        except Exception as error:
            observation = {"status": "error", "tool": tool_name, "error": str(error)}

        observations.append(observation)
        entry["observation"] = observation
        trace.append(entry)

    return {"answer": None, "trace": trace, "finish_reason": "max_steps"}

