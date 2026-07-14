from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agent_loop import ModelResponse, ScriptedModel, ToolCall, run_agent

if __name__ == "__main__":
    calls = [ToolCall("c1", "calculator", {"expression": "6 * 7"}), ToolCall("c2", "time", {})]
    model = ScriptedModel([ModelResponse(tool_calls=calls), ModelResponse("42 at 12:00")])
    result = run_agent("two facts", model, {"calculator": lambda expression: "42", "time": lambda: "12:00"})
    print(f"same_round_tools={len(result['tool_results'])} answer={result['answer']}")

