from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from course_runtime import (  # noqa: E402
    Agent,
    LLMResponse,
    Runner,
    ScriptedLLM,
    ToolCall,
    ToolSpec,
)


llm = ScriptedLLM([
    LLMResponse(
        tool_calls=[ToolCall("c1", "echo", {"text": "42"})],
        continuation_items=[{"type": "function_call", "call_id": "c1"}],
        finish_reason="tool_calls",
    ),
    LLMResponse(content="The result is 42.", finish_reason="completed"),
])
agent = Agent(
    "runtime-demo",
    "Use the provided tool.",
    llm,
    [ToolSpec("echo", "Echo text.", {"type": "object"}, lambda text: text)],
)
result = Runner().run(agent, "Return 42")
print(
    f"answer={result.content!r} steps={result.steps} "
    f"tools={len(result.tool_results)} events={len(result.events)} "
    f"finish_reason={result.finish_reason}"
)
