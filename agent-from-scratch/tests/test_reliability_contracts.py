from __future__ import annotations

from pathlib import Path

import pytest

from agent_from_scratch.agent import Agent
from agent_from_scratch.llm import FakeLLM
from agent_from_scratch.runner import Runner
from agent_from_scratch.schemas import LLMResponse, ToolCall, ToolResult
from agent_from_scratch.session import (
    CheckpointStore,
    ContextWindow,
    RunCheckpoint,
    Session,
    SessionStore,
)
from agent_from_scratch.tools import ToolContext, ToolSpec


def test_formal_session_round_trip_preserves_turn_identity(tmp_path: Path) -> None:
    session = Session("session-turns")

    turn = session.start_turn("inspect the project")
    session.append_assistant(turn.id, "inspection complete")
    store = SessionStore(tmp_path / "sessions")
    store.save(session)

    restored = store.load(session.id)
    assert [message.role for message in restored.messages] == ["user", "assistant"]
    assert [message.content for message in restored.messages] == [
        "inspect the project",
        "inspection complete",
    ]
    assert {message.turn_id for message in restored.messages} == {turn.id}


def test_context_window_returns_budget_metadata() -> None:
    session = Session("session-context")
    old_turn = session.start_turn("a" * 24)
    session.append_assistant(old_turn.id, "b" * 24)
    latest_turn = session.start_turn("latest")

    result = ContextWindow(max_chars=31).build(session.messages)

    assert result.truncated is True
    assert result.used_chars == sum(len(message.content) for message in result.messages)
    assert result.used_chars <= 31
    assert result.messages[-1].turn_id == latest_turn.id
    assert result.messages[0].role == "system"


def test_context_window_rejects_one_message_larger_than_the_budget() -> None:
    session = Session("session-oversized")
    session.start_turn("x" * 11)

    with pytest.raises(ValueError, match="(?i)message.*budget|budget.*message"):
        ContextWindow(max_chars=10).build(session.messages)


def test_resume_reuses_completed_tool_result_without_repeating_side_effect(
    tmp_path: Path,
) -> None:
    calls = 0

    def side_effect(*, context: ToolContext) -> str:
        nonlocal calls
        del context
        calls += 1
        return "executed again"

    tool = ToolSpec(
        name="side_effect",
        description="A deterministic side effect used to verify resume idempotency.",
        parameters={
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
        handler=side_effect,
    )
    completed = ToolResult(
        call_id="call-completed",
        name="side_effect",
        status="success",
        output="persisted output",
    )
    checkpoint = RunCheckpoint(
        run_id="run-resume-once",
        user_input="perform the operation once",
        input_items=[
            {"role": "system", "content": "test"},
            {"role": "user", "content": "perform the operation once"},
        ],
        events=[],
        tool_results=[completed],
        next_step=1,
        completed_calls={completed.call_id: completed},
    )
    store = CheckpointStore(tmp_path / "checkpoints")
    store.save(checkpoint)
    llm = FakeLLM(
        [
            LLMResponse(
                tool_calls=[ToolCall("call-completed", "side_effect", {})],
                finish_reason="tool_calls",
            ),
            LLMResponse(content="done", finish_reason="completed"),
        ]
    )
    agent = Agent("resume-test", "test", llm, [tool], max_steps=2)

    result = Runner(checkpoint_store=store).resume(
        agent,
        checkpoint.run_id,
        context=ToolContext(workspace=tmp_path),
    )

    assert result.finish_reason == "completed"
    assert calls == 0
    assert result.tool_results == [completed]
    second_request_items = llm.requests[1]["messages"]
    cached_outputs = [
        item
        for item in second_request_items
        if item.get("type") == "function_call_output"
        and item.get("call_id") == completed.call_id
    ]
    assert len(cached_outputs) == 1
    assert "persisted output" in cached_outputs[0]["output"]


def test_runner_rejects_too_many_tool_calls_in_one_model_step(tmp_path: Path) -> None:
    calls = [ToolCall(f"call-{index}", "noop", {}) for index in range(17)]
    tool = ToolSpec(
        name="noop",
        description="A read-only no-op.",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
        handler=lambda *, context: "ok",
        risk="read",
    )
    agent = Agent(
        "bounded",
        "test",
        FakeLLM([LLMResponse(tool_calls=calls, finish_reason="tool_calls")]),
        [tool],
        max_steps=1,
    )

    result = Runner(max_tool_calls_per_step=16).run(
        agent,
        "do too much",
        context=ToolContext(workspace=tmp_path),
    )

    assert result.finish_reason == "error"
    assert result.tool_results == []
    assert any(event.type == "tool_call_limit_exceeded" for event in result.events)
