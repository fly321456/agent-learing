from multi_agent_lab import (
    ReviewCase, TaskAudit, audit_task, compare_single_and_reviewer, decide_from_comparison,
)

audit = audit_task(TaskAudit(True, True, True, True, True))
cases = [
    ReviewCase("complete", "implementation and tests", ("implementation", "tests")),
    ReviewCase("missing-test", "implementation only", ("implementation", "tests")),
]
comparison = compare_single_and_reviewer(cases)
decision = decide_from_comparison(comparison)
print(f"audit={str(audit.use_multi_agent).lower()} measured_decision={str(decision.use_multi_agent).lower()}")
print(
    f"single_false_accepts={comparison.single_false_accepts} "
    f"reviewer_false_accepts={comparison.reviewer_false_accepts} "
    f"communication_chars={comparison.communication_chars}"
)
