from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from course_runtime import LLMResponse, ScriptedLLM, ToolCall  # noqa: E402


llm = ScriptedLLM([
    LLMResponse(
        tool_calls=[ToolCall("call-1", "read_file", {"path": "README.md"})],
        continuation_items=[{"vendor_item": "opaque"}],
        finish_reason="tool_calls",
    )
])
response = llm.generate([{"role": "user", "content": "inspect"}])
print(f"model_call tools={len(response.tool_calls)} continuation={len(response.continuation_items)}")
