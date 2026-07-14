from pathlib import Path
import sys
import tempfile


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from course_tools import ToolCall, ToolContext, ToolManager, create_coding_tools  # noqa: E402


with tempfile.TemporaryDirectory() as directory:
    manager = ToolManager(create_coding_tools())
    denied = manager.execute(
        ToolCall("d1", "run_command", {"command": [sys.executable, "-c", "print('no')"]}),
        ToolContext(Path(directory), approval=lambda _tool, _args: False),
    )
    timed_out = manager.execute(
        ToolCall("t1", "run_command", {
            "command": [sys.executable, "-c", "import time; time.sleep(1)"]
        }),
        ToolContext(Path(directory), approval=lambda _tool, _args: True, command_timeout=0.3),
    )
    print(f"approval={denied.status} command={timed_out.status}")
