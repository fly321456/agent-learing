import json

from agent_from_scratch.agent import Agent
from agent_from_scratch.errors import LLMError, RetryableLLMError
from agent_from_scratch.llm import BaseLLM
from agent_from_scratch.runner import RetryPolicy, Runner
from agent_from_scratch.schemas import LLMResponse
from agent_from_scratch.tools import ToolContext
from agent_from_scratch.tracing import JsonlTraceWriter


class FlakyLLM(BaseLLM):
    def __init__(self):
        self.calls = 0

    def generate(self, messages, tools=None):
        self.calls += 1
        if self.calls == 1:
            raise RetryableLLMError("temporary failure")
        return LLMResponse(content="recovered", finish_reason="completed")


class InvalidLLM(BaseLLM):
    def __init__(self):
        self.calls = 0

    def generate(self, messages, tools=None):
        self.calls += 1
        raise LLMError("invalid response")


def test_runner_retries_model_calls_and_records_retry_event(tmp_path):
    llm = FlakyLLM()
    agent = Agent("test", "test", llm, max_steps=1)

    result = Runner(retry_policy=RetryPolicy(attempts=2, base_delay=0)).run(
        agent, "hello", context=ToolContext(workspace=tmp_path)
    )

    assert result.content == "recovered"
    assert llm.calls == 2
    assert "llm_retry" in [event.type for event in result.events]


def test_jsonl_trace_writer_persists_each_event(tmp_path):
    trace_path = tmp_path / "traces" / "run.jsonl"
    writer = JsonlTraceWriter(trace_path)
    agent = Agent("test", "test", FlakyLLM(), max_steps=1)

    result = Runner(retry_policy=RetryPolicy(attempts=2, base_delay=0)).run(
        agent,
        "hello",
        context=ToolContext(workspace=tmp_path),
        event_sink=writer,
    )
    records = [json.loads(line) for line in trace_path.read_text(encoding="utf-8").splitlines()]

    assert len(records) == len(result.events)
    assert records[0]["type"] == "run_started"
    assert records[-1]["data"]["finish_reason"] == "completed"


def test_runner_does_not_retry_deterministic_model_errors(tmp_path):
    llm = InvalidLLM()
    agent = Agent("test", "test", llm, max_steps=1)

    result = Runner(retry_policy=RetryPolicy(attempts=3, base_delay=0)).run(
        agent, "hello", context=ToolContext(workspace=tmp_path)
    )

    assert result.finish_reason == "error"
    assert llm.calls == 1
    assert "llm_retry" not in [event.type for event in result.events]
