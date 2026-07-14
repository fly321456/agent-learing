from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from course_observability import evaluate_cases, load_cases  # noqa: E402


cases = load_cases(ROOT / "cases.json")
metrics = evaluate_cases(cases, lambda case: list(case.expected_tools))
print(
    f"total={metrics.total} passed={metrics.passed} rate={metrics.success_rate:.0%} "
    f"tool_calls={metrics.tool_calls} steps={metrics.steps}"
)
