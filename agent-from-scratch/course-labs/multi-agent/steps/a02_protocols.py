from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from multi_agent_lab import create_plan, execute_plan  # noqa: E402

plan = create_plan(["inspect", "test", "document"])
state = execute_plan(plan, lambda item: f"done:{item.objective}")
print(f"planned={len(plan)} completed={sum(result.status == 'success' for result in state.results)}")
