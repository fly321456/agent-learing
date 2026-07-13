from pathlib import Path
import subprocess
import sys
import tempfile


def workspace_path(workspace: Path, relative: str) -> Path:
    target = (workspace / relative).resolve()
    target.relative_to(workspace.resolve())
    return target


with tempfile.TemporaryDirectory() as directory:
    workspace = Path(directory).resolve()
    source = workspace / "demo.py"
    source.write_text("value = 1\n", encoding="utf-8")
    try:
        workspace_path(workspace, "../outside.py")
    except ValueError:
        print("outside=blocked")
    text = source.read_text(encoding="utf-8")
    source.write_text(text.replace("value = 1", "value = 2"), encoding="utf-8")
    completed = subprocess.run(
        [sys.executable, "-c", "from demo import value; assert value == 2"],
        cwd=workspace,
        check=False,
    )
    print(f"patch=success test_exit={completed.returncode}")

