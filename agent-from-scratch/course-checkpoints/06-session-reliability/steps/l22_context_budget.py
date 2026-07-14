from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from course_reliability import ContextWindow, Message  # noqa: E402


messages = [Message("user", "old" * 20, "t1"), Message("user", "latest", "t2")]
result = ContextWindow(20).build(messages, summary="earlier task")
print(f"truncated={str(result.truncated).lower()} kept={len(result.messages)} latest={result.messages[-1].content}")
