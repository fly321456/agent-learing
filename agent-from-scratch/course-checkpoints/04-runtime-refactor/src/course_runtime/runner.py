from __future__ import annotations

from dataclasses import asdict
import json
from uuid import uuid4

from .agent import Agent
from .schemas import Event, RunResult, ToolResult
from .tools import ToolManager


class Runner:
    def run(self, agent: Agent, user_input: str) -> RunResult:
        run_id = str(uuid4())
        events: list[Event] = []
        tool_results: list[ToolResult] = []
        messages: list = [
            {"role": "system", "content": agent.instructions},
            {"role": "user", "content": user_input},
        ]
        manager = ToolManager(agent.tools)

        def emit(event_type: str, step: int, **data) -> None:
            events.append(Event(event_type, len(events) + 1, run_id, step, data))

        def finish(content: str, steps: int, reason: str) -> RunResult:
            emit("run_completed", steps, finish_reason=reason)
            return RunResult(content, events, tool_results, steps, reason, run_id)

        emit("run_started", 0, agent=agent.name)
        for step in range(1, agent.max_steps + 1):
            emit("llm_started", step)
            try:
                response = agent.llm.generate(messages, tools=manager.schemas)
            except Exception as exc:
                emit("llm_failed", step, error=str(exc))
                return finish("", step, "error")

            emit(
                "llm_completed",
                step,
                finish_reason=response.finish_reason,
                tool_call_count=len(response.tool_calls),
            )
            messages.extend(response.continuation_items)
            if not response.tool_calls:
                return finish(response.content, step, "completed")

            for call in response.tool_calls:
                emit("tool_called", step, call_id=call.id, name=call.name)
                result = manager.execute(call)
                tool_results.append(result)
                emit("tool_completed", step, **asdict(result))
                messages.append({
                    "type": "function_call_output",
                    "call_id": call.id,
                    "output": json.dumps(asdict(result), ensure_ascii=False),
                })

        return finish("", agent.max_steps, "max_steps")
