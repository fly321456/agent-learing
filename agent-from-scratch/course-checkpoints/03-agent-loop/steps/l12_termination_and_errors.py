from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agent_loop import ModelResponse, ScriptedModel, ToolCall, run_agent

if __name__ == "__main__":
    response = ModelResponse(tool_calls=[ToolCall("c1", "missing", {})])
    result = run_agent("stop safely", ScriptedModel([response], repeat_last=True), {}, max_steps=2)
    print(f"status={result['tool_results'][0]['status']} finish_reason={result['finish_reason']}")

