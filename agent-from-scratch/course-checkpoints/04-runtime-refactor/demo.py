from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from course_runtime import (  # noqa: E402
    Agent,
    LLMResponse,
    Runner,
    ScriptedLLM,
    ToolCall,
    ToolSpec,
)


def main() -> None:
    llm = ScriptedLLM([
        LLMResponse(
            tool_calls=[ToolCall("call-1", "calculator", {"expression": "6 * 7"})],
            continuation_items=[{"type": "function_call", "call_id": "call-1"}],
            finish_reason="tool_calls",
        ),
        LLMResponse(content="42", finish_reason="completed"),
    ])
    tool = ToolSpec(
        "calculator",
        "Evaluate the lesson expression.",
        {"type": "object", "properties": {"expression": {"type": "string"}}},
        lambda expression: str(eval(expression, {"__builtins__": {}}, {})),
    )
    result = Runner().run(Agent("runtime-demo", "Calculate safely.", llm, [tool]), "6 * 7")
    print(
        f"content={result.content} steps={result.steps} tools={len(result.tool_results)} "
        f"events={len(result.events)} finish_reason={result.finish_reason}"
    )


if __name__ == "__main__":
    main()
