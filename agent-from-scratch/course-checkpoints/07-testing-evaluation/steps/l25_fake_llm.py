from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from course_observability import FakeLLM  # noqa: E402


fake = FakeLLM([{"content": "first"}, {"content": "second"}])
first = fake.generate([{"role": "user", "content": "one"}])
second = fake.generate([{"role": "user", "content": "two"}])
print(f"responses={first['content']},{second['content']} requests={len(fake.requests)}")
