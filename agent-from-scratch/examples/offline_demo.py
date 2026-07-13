from pathlib import Path

from agent_from_scratch import Agent, LLMResponse, Runner, ToolCall
from agent_from_scratch.llm import FakeLLM
from agent_from_scratch.tools import ToolContext, create_default_tools


llm = FakeLLM(
    [
        LLMResponse(
            tool_calls=[ToolCall("demo-1", "calculator", {"expression": "6 * 7"})],
            continuation_items=[{"type": "function_call", "call_id": "demo-1"}],
        ),
        LLMResponse(content="6 * 7 = 42", finish_reason="completed"),
    ]
)
agent = Agent("offline-demo", "Use tools when useful.", llm, create_default_tools())
result = Runner().run(agent, "Calculate 6 * 7", context=ToolContext(Path.cwd()))
print(result.content)

