from agent_from_scratch.agent import Agent
from agent_from_scratch.llm import FakeLLM
from agent_from_scratch.runner import Runner
from agent_from_scratch.schemas import LLMResponse, ToolCall
from agent_from_scratch.tools import ToolContext, ToolManager, create_default_tools


def test_runner_returns_run_result_and_accumulates_events(tmp_path):
    llm = FakeLLM(
        [
            LLMResponse(
                tool_calls=[
                    ToolCall(id="call-1", name="calculator", arguments={"expression": "2 + 3"})
                ],
                continuation_items=[{"type": "function_call", "call_id": "call-1"}],
                finish_reason="tool_calls",
            ),
            LLMResponse(content="The answer is 5.", finish_reason="completed"),
        ]
    )
    agent = Agent(
        name="test-agent",
        instructions="Be concise.",
        llm=llm,
        tools=create_default_tools(),
        max_steps=4,
    )
    observed = []

    result = Runner().run(
        agent,
        "Calculate 2 + 3",
        context=ToolContext(workspace=tmp_path),
        event_sink=observed.append,
    )

    assert result.content == "The answer is 5."
    assert result.finish_reason == "completed"
    assert result.steps == 2
    assert result.tool_results[0].output == "5"
    assert [event.type for event in result.events] == [
        "run_started",
        "llm_started",
        "llm_completed",
        "tool_called",
        "tool_completed",
        "llm_started",
        "llm_completed",
        "run_completed",
    ]
    assert observed == result.events
    assert [event.sequence for event in result.events] == list(range(1, 9))


def test_runner_uses_continuation_items_instead_of_raw_response(tmp_path):
    class ExplodingRawResponse:
        def __getattribute__(self, name):
            raise AssertionError(f"Runner accessed raw_response.{name}")

    llm = FakeLLM(
        [
            LLMResponse(
                tool_calls=[ToolCall(id="call-1", name="calculator", arguments={"expression": "1"})],
                continuation_items=[{"type": "function_call", "call_id": "call-1"}],
                raw_response=ExplodingRawResponse(),
            ),
            LLMResponse(content="done", finish_reason="completed"),
        ]
    )
    agent = Agent("test", "test", llm, create_default_tools(), max_steps=2)

    result = Runner().run(agent, "run", context=ToolContext(workspace=tmp_path))

    assert result.finish_reason == "completed"
    assert llm.requests[1]["messages"][2]["call_id"] == "call-1"


def test_runner_stops_at_max_steps(tmp_path):
    response = LLMResponse(
        tool_calls=[ToolCall(id="repeat", name="calculator", arguments={"expression": "1"})],
        continuation_items=[{"type": "function_call", "call_id": "repeat"}],
    )
    llm = FakeLLM([response], repeat_last=True)
    agent = Agent("test", "test", llm, create_default_tools(), max_steps=2)

    result = Runner().run(agent, "loop", context=ToolContext(workspace=tmp_path))

    assert result.finish_reason == "max_steps"
    assert result.steps == 2
    assert result.content == ""


def test_runner_returns_denied_when_risky_tool_is_not_approved(tmp_path):
    llm = FakeLLM(
        [
            LLMResponse(
                tool_calls=[
                    ToolCall(
                        id="write-1",
                        name="apply_patch",
                        arguments={"path": "demo.txt", "old_text": "old", "new_text": "new"},
                    )
                ]
            )
        ]
    )
    agent = Agent("test", "test", llm, create_default_tools(), max_steps=2)

    result = Runner().run(agent, "edit", context=ToolContext(workspace=tmp_path))

    assert result.finish_reason == "denied"
    assert result.tool_results[0].status == "denied"

