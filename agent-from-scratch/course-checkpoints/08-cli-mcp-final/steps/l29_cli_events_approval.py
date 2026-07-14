from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from course_product import Event, format_event, request_approval  # noqa: E402


event = Event("tool_completed", 4, "run-1", 2, {"name": "apply_patch", "status": "success"})
denied = request_approval("run_command", {"command": ["pytest"]}, lambda _prompt: "")
print(f"event={format_event(event)} approval={str(denied).lower()}")
