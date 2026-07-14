from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from multi_agent_lab import TaskAudit, audit_task  # noqa: E402

decision = audit_task(TaskAudit(True, True, True, True, True))
print(f"use_multi_agent={str(decision.use_multi_agent).lower()} reasons={len(decision.reasons)}")
