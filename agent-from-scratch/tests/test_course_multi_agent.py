from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys


LAB = Path(__file__).resolve().parents[1] / "course-labs" / "multi-agent"


def load_lab():
    path = LAB / "multi_agent_lab.py"
    spec = importlib.util.spec_from_file_location("course_multi_agent_lab", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_decomposability_audit_rejects_tightly_coupled_unmeasured_task() -> None:
    lab = load_lab()
    audit = lab.TaskAudit(
        independent_subtasks=False,
        distinct_expertise=False,
        parallelizable=False,
        low_shared_state=True,
        evaluation_available=False,
    )
    decision = lab.audit_task(audit)
    assert decision.use_multi_agent is False
    assert "evaluation" in " ".join(decision.reasons).lower()


def test_planner_executor_preserves_success_when_one_subtask_fails() -> None:
    lab = load_lab()
    plan = lab.create_plan(["inspect", "test", "document"])

    def execute(item):
        if item.objective == "test":
            raise RuntimeError("tests unavailable")
        return f"done:{item.objective}"

    state = lab.execute_plan(plan, execute)
    assert [result.status for result in state.results] == ["success", "error", "success"]
    assert state.results[0].output == "done:inspect"
    assert state.results[2].output == "done:document"


def test_shared_state_measures_communication_cost() -> None:
    lab = load_lab()
    state = lab.SharedState()
    state.record("planner", "executor", "inspect config")
    state.record("executor", "reviewer", "config inspected")
    assert state.message_count == 2
    assert state.communication_chars == len("inspect config") + len("config inspected")


def test_reviewer_reduces_false_accepts_but_is_not_always_recommended() -> None:
    lab = load_lab()
    cases = [
        lab.ReviewCase("good", "code plus tests", ("code", "tests")),
        lab.ReviewCase("missing-tests", "code only", ("code", "tests")),
    ]
    comparison = lab.compare_single_and_reviewer(cases)
    assert comparison.single_false_accepts == 1
    assert comparison.reviewer_false_accepts == 0
    assert comparison.communication_chars > 0
    assert lab.decide_from_comparison(comparison).use_multi_agent is True

    no_gain = lab.Comparison(0, 0, 100)
    assert lab.decide_from_comparison(no_gain).use_multi_agent is False


def test_multi_agent_steps_and_demo_run_offline() -> None:
    scripts = sorted((LAB / "steps").glob("a*.py"))
    assert [path.name[:3] for path in scripts] == ["a01", "a02", "a03", "a04"]
    for script in scripts + [LAB / "demo.py"]:
        completed = subprocess.run(
            [sys.executable, str(script)], cwd=script.parent, capture_output=True,
            text=True, encoding="utf-8", errors="strict", timeout=10, check=False,
        )
        assert completed.returncode == 0, completed.stderr
        assert completed.stdout.strip()
