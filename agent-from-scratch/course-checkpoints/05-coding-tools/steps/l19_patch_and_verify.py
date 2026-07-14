from pathlib import Path
import sys
import tempfile


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from course_tools import ToolCall, ToolContext, ToolManager, create_coding_tools  # noqa: E402


with tempfile.TemporaryDirectory() as directory:
    workspace = Path(directory)
    (workspace / "app.py").write_text("value = 1\n", encoding="utf-8")
    manager = ToolManager(create_coding_tools())
    context = ToolContext(workspace, approval=lambda _tool, _args: True)
    patch = manager.execute(ToolCall("p1", "apply_patch", {
        "path": "app.py", "old_text": "value = 1", "new_text": "value = 2"
    }), context)
    verify = manager.execute(ToolCall("v1", "run_command", {
        "command": [sys.executable, "-c", "from app import value; assert value == 2"]
    }), context)
    print(f"patch={patch.status} verify={verify.status} exit_code={verify.exit_code or 0}")
