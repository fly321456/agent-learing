from pathlib import Path
import subprocess
import sys
import tempfile


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from course_observability import run_repository_e2e  # noqa: E402


with tempfile.TemporaryDirectory() as directory:
    workspace = Path(directory)
    subprocess.run(["git", "init", "-q"], cwd=workspace, check=True)
    (workspace / "app.py").write_text("value = 1\n", encoding="utf-8")
    (workspace / "test_app.py").write_text(
        "from app import value\n\ndef test_value():\n    assert value == 2\n", encoding="utf-8"
    )
    result = run_repository_e2e(workspace)
    print(f"passed={str(result.passed).lower()} actions={','.join(result.actions)}")
