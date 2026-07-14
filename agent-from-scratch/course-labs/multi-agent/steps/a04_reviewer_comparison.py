from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from multi_agent_lab import ReviewCase, compare_single_and_reviewer, decide_from_comparison  # noqa: E402

cases = [
    ReviewCase("good", "code plus tests", ("code", "tests")),
    ReviewCase("bad", "code only", ("code", "tests")),
]
comparison = compare_single_and_reviewer(cases)
decision = decide_from_comparison(comparison)
print(
    f"single_false_accepts={comparison.single_false_accepts} "
    f"reviewer_false_accepts={comparison.reviewer_false_accepts} "
    f"recommended={str(decision.use_multi_agent).lower()}"
)
