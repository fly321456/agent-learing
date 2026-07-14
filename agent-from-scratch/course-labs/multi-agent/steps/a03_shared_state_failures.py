from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from multi_agent_lab import SharedState, create_plan, execute_plan  # noqa: E402

def executor(item):
    if item.objective == "test":
        raise RuntimeError("unavailable")
    return "done"

state = execute_plan(create_plan(["inspect", "test", "document"]), executor)
shared = SharedState()
shared.record("planner", "executor", "three tasks")
print(f"success=2 failures=1 messages={shared.message_count} chars={shared.communication_chars}")
