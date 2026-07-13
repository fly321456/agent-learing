from dataclasses import asdict, dataclass
import json
from pathlib import Path
import time
from typing import Callable
from uuid import uuid4

from .agent import Agent
from .errors import RetryableLLMError
from .schemas import Event, RunResult, ToolResult
from .session import CheckpointStore, RunCheckpoint
from .tools import ToolContext, ToolManager


EventSink = Callable[[Event], None]


@dataclass(frozen=True)
class RetryPolicy:
    attempts: int = 1
    base_delay: float = 0.25

    def __post_init__(self) -> None:
        if self.attempts < 1:
            raise ValueError("attempts must be at least 1")
        if self.base_delay < 0:
            raise ValueError("base_delay cannot be negative")


class Runner:
    def __init__(
        self,
        *,
        retry_policy: RetryPolicy | None = None,
        checkpoint_store: CheckpointStore | None = None,
    ):
        self.retry_policy = retry_policy or RetryPolicy()
        self.checkpoint_store = checkpoint_store

    def run(
        self,
        agent: Agent,
        user_input: str,
        *,
        context: ToolContext | None = None,
        event_sink: EventSink | None = None,
        history: list[dict[str, str]] | None = None,
    ) -> RunResult:
        run_id = str(uuid4())
        input_items: list = [
            {"role": "system", "content": agent.instructions},
        ]
        input_items.extend(history or [])
        input_items.append({"role": "user", "content": user_input})
        return self._run_loop(
            agent=agent,
            user_input=user_input,
            input_items=input_items,
            events=[],
            tool_results=[],
            run_id=run_id,
            start_step=1,
            context=context or ToolContext(workspace=Path.cwd()),
            event_sink=event_sink,
            resumed=False,
        )

    def resume(
        self,
        agent: Agent,
        run_id: str,
        *,
        context: ToolContext | None = None,
        event_sink: EventSink | None = None,
    ) -> RunResult:
        if self.checkpoint_store is None:
            raise ValueError("Runner requires a CheckpointStore to resume a run")
        checkpoint = self.checkpoint_store.load(run_id)
        return self._run_loop(
            agent=agent,
            user_input=checkpoint.user_input,
            input_items=checkpoint.input_items,
            events=checkpoint.events,
            tool_results=checkpoint.tool_results,
            run_id=checkpoint.run_id,
            start_step=checkpoint.next_step,
            context=context or ToolContext(workspace=Path.cwd()),
            event_sink=event_sink,
            resumed=True,
        )

    def _run_loop(
        self,
        *,
        agent: Agent,
        user_input: str,
        input_items: list,
        events: list[Event],
        tool_results: list[ToolResult],
        run_id: str,
        start_step: int,
        context: ToolContext,
        event_sink: EventSink | None,
        resumed: bool,
    ) -> RunResult:
        manager = ToolManager(agent.tools)

        def emit(event_type: str, step: int, **data) -> None:
            event = Event(event_type, len(events) + 1, run_id, step, data)
            events.append(event)
            if event_sink is not None:
                event_sink(event)

        def finish(content: str, steps: int, reason: str) -> RunResult:
            emit("run_completed", steps, finish_reason=reason)
            return RunResult(
                content=content,
                events=events,
                tool_results=tool_results,
                steps=steps,
                finish_reason=reason,
                run_id=run_id,
            )

        if resumed:
            emit("run_resumed", start_step - 1)
        else:
            emit("run_started", 0, agent=agent.name)

        end_step = start_step + agent.max_steps - 1
        for step in range(start_step, end_step + 1):
            emit("llm_started", step)
            try:
                response = self._generate(agent, input_items, manager.schemas, emit, step)
            except Exception as exc:
                emit("llm_failed", step, error=str(exc))
                return finish("", step, "error")

            emit(
                "llm_completed",
                step,
                finish_reason=response.finish_reason,
                tool_call_count=len(response.tool_calls),
            )
            input_items.extend(response.continuation_items)

            if not response.tool_calls:
                return finish(response.content, step, response.finish_reason or "completed")

            for tool_call in response.tool_calls:
                emit(
                    "tool_called",
                    step,
                    call_id=tool_call.id,
                    name=tool_call.name,
                    arguments=tool_call.arguments,
                )
                result = manager.execute(tool_call, context)
                tool_results.append(result)
                emit("tool_completed", step, **asdict(result))

                if result.status == "denied":
                    return finish("", step, "denied")

                input_items.append(
                    {
                        "type": "function_call_output",
                        "call_id": tool_call.id,
                        "output": json.dumps(asdict(result), ensure_ascii=False),
                    }
                )

            self._save_checkpoint(
                run_id,
                user_input,
                input_items,
                events,
                tool_results,
                next_step=step + 1,
            )

        return finish("", end_step, "max_steps")

    def _generate(self, agent, input_items, schemas, emit, step):
        for attempt in range(1, self.retry_policy.attempts + 1):
            try:
                return agent.llm.generate(input_items, tools=schemas)
            except RetryableLLMError as exc:
                if attempt >= self.retry_policy.attempts:
                    raise
                emit("llm_retry", step, attempt=attempt, error=str(exc))
                delay = self.retry_policy.base_delay * (2 ** (attempt - 1))
                if delay:
                    time.sleep(delay)
        raise RuntimeError("retry loop ended unexpectedly")

    def _save_checkpoint(
        self,
        run_id,
        user_input,
        input_items,
        events,
        tool_results,
        *,
        next_step,
    ) -> None:
        if self.checkpoint_store is None:
            return
        self.checkpoint_store.save(
            RunCheckpoint(
                run_id=run_id,
                user_input=user_input,
                input_items=list(input_items),
                events=list(events),
                tool_results=list(tool_results),
                next_step=next_step,
            )
        )
