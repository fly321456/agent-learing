from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from course_runtime import ToolCall, ToolManager, ToolSpec  # noqa: E402


manager = ToolManager([
    ToolSpec("echo", "Echo text.", {"type": "object"}, lambda text: text),
])
success = manager.execute(ToolCall("c1", "echo", {"text": "observed"}))
unknown = manager.execute(ToolCall("c2", "missing", {}))
print(f"success={success.status}:{success.output} unknown={unknown.status}:{unknown.error}")
