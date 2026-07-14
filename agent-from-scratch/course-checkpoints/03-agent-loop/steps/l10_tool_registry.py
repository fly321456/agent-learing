from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agent_loop import ModelResponse, ScriptedModel, ToolCall, run_agent

TOOLS = {"calculator": lambda expression: "42" if expression == "6 * 7" else "unsupported"}
if __name__ == "__main__":
    model = ScriptedModel([ModelResponse(tool_calls=[ToolCall("c1", "calculator", {"expression": "6 * 7"})]), ModelResponse("42")])
    result = run_agent("calculate", model, TOOLS)
    print(f"tool={result['tool_results'][0]['name']} output={result['tool_results'][0]['output']}")

