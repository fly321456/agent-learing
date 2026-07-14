from pathlib import Path
import sys
import tempfile


sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from course_tools import (  # noqa: E402
    ToolCall, ToolContext, ToolManager, WorkspaceBoundaryError,
    create_coding_tools, read_file,
)


def main() -> None:
    with tempfile.TemporaryDirectory() as directory:
        workspace = Path(directory)
        (workspace / "app.py").write_text("value = 1\n", encoding="utf-8")
        context = ToolContext(workspace, approval=lambda _tool, _args: True)
        manager = ToolManager(create_coding_tools())
        try:
            read_file(context=context, path="../outside.py")
        except WorkspaceBoundaryError:
            print("outside=blocked")
        patched = manager.execute(ToolCall("p1", "apply_patch", {
            "path": "app.py", "old_text": "value = 1", "new_text": "value = 2"
        }), context)
        tested = manager.execute(ToolCall("t1", "run_command", {
            "command": [sys.executable, "-c", "from app import value; assert value == 2"]
        }), context)
        print(f"patch={patched.status} test={tested.status} exit_code={tested.exit_code or 0}")


if __name__ == "__main__":
    main()
