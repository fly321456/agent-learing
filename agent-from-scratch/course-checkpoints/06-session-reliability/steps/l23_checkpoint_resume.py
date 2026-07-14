from pathlib import Path
import sys
import tempfile


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from course_reliability import CheckpointStore, RunCheckpoint, execute_once  # noqa: E402


with tempfile.TemporaryDirectory() as directory:
    calls = []
    checkpoint = RunCheckpoint("run-1", 2)
    first = execute_once(checkpoint, "patch-1", lambda: calls.append("write") or "patched")
    store = CheckpointStore(Path(directory))
    store.save(checkpoint)
    restored = store.load("run-1")
    second = execute_once(restored, "patch-1", lambda: calls.append("duplicate") or "bad")
    print(f"first={first} resumed={second} side_effects={len(calls)} next_step={restored.next_step}")
