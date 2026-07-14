from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from course_reliability import RetryableError, RetryPolicy, RuntimeConfig  # noqa: E402


calls = 0


def flaky() -> str:
    global calls
    calls += 1
    if calls == 1:
        raise RetryableError("temporary")
    return "recovered"


config = RuntimeConfig.from_mapping({"AGENT_RETRY_ATTEMPTS": "2"})
result = RetryPolicy(config.retry_attempts, base_delay=0).run(flaky)
print(f"attempts={calls} result={result} max_steps={config.max_steps}")
