from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agent_loop import ModelResponse, ScriptedModel, ToolCall, run_agent

if __name__ == "__main__":
    model = ScriptedModel([ModelResponse(tool_calls=[ToolCall("c1", "ping", {})]), ModelResponse("done")])
    result = run_agent("ping once", model, {"ping": lambda: "pong"})
    print(f"steps={result['steps']} finish_reason={result['finish_reason']}")

