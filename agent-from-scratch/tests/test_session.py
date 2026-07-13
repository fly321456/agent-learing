from agent_from_scratch.agent import Agent
from agent_from_scratch.llm import FakeLLM
from agent_from_scratch.runner import Runner
from agent_from_scratch.schemas import LLMResponse, ToolCall
from agent_from_scratch.session import CheckpointStore, ContextWindow, Session, SessionStore
from agent_from_scratch.tools import ToolContext, create_default_tools


def test_session_store_round_trips_utf8_messages(tmp_path):
    store = SessionStore(tmp_path / ".agent" / "sessions")
    session = Session("session-1")
    session.append("user", "读取课程")
    session.append("assistant", "可以")

    store.save(session)
    restored = store.load("session-1")

    assert restored == session


def test_context_window_keeps_recent_messages_with_explicit_truncation_marker():
    messages = [
        {"role": "user", "content": "a" * 30},
        {"role": "assistant", "content": "b" * 30},
        {"role": "user", "content": "latest"},
    ]

    trimmed = ContextWindow(max_chars=40).trim(messages)

    assert trimmed[0]["role"] == "system"
    assert "truncated" in trimmed[0]["content"]
    assert trimmed[-1] == {"role": "user", "content": "latest"}


def test_runner_can_resume_from_a_persisted_checkpoint(tmp_path):
    checkpoint_store = CheckpointStore(tmp_path / ".agent" / "checkpoints")
    first_llm = FakeLLM(
        [
            LLMResponse(
                tool_calls=[ToolCall("call-1", "calculator", {"expression": "2 + 2"})],
                continuation_items=[{"type": "function_call", "call_id": "call-1"}],
            )
        ]
    )
    first_agent = Agent("test", "test", first_llm, create_default_tools(), max_steps=1)
    runner = Runner(checkpoint_store=checkpoint_store)

    first_result = runner.run(
        first_agent, "calculate", context=ToolContext(workspace=tmp_path)
    )
    resumed_agent = Agent(
        "test",
        "test",
        FakeLLM([LLMResponse(content="4", finish_reason="completed")]),
        create_default_tools(),
        max_steps=1,
    )
    resumed = runner.resume(
        resumed_agent,
        first_result.run_id,
        context=ToolContext(workspace=tmp_path),
    )

    assert first_result.finish_reason == "max_steps"
    assert resumed.finish_reason == "completed"
    assert resumed.content == "4"
    assert resumed.steps == 2
    assert resumed.events[-1].sequence == len(resumed.events)

