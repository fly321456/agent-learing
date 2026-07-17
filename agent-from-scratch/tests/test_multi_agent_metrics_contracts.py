from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


LAB = Path(__file__).resolve().parents[1] / "course-labs" / "multi-agent"


def load_lab():
    path = LAB / "multi_agent_lab.py"
    spec = importlib.util.spec_from_file_location("course_multi_agent_metrics", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_reviewer_metrics_use_independent_truth_and_expose_both_error_types() -> None:
    lab = load_lab()
    cases = [
        lab.ReviewCase(
            "false-accept",
            "code plus tests",
            ("code", "tests"),
            actual_valid=False,
        ),
        lab.ReviewCase(
            "false-reject",
            "semantically complete solution",
            ("literal-token",),
            actual_valid=True,
        ),
    ]

    comparison = lab.compare_single_and_reviewer(cases)

    assert comparison.single_false_accepts == 1
    assert comparison.reviewer_false_accepts == 1
    assert comparison.reviewer_false_rejects == 1


def test_reviewer_can_have_no_errors_against_independent_truth() -> None:
    lab = load_lab()
    cases = [
        lab.ReviewCase(
            "valid",
            "code plus tests",
            ("code", "tests"),
            actual_valid=True,
        ),
        lab.ReviewCase(
            "invalid",
            "code only",
            ("code", "tests"),
            actual_valid=False,
        ),
    ]

    comparison = lab.compare_single_and_reviewer(cases)

    assert comparison.single_false_accepts == 1
    assert comparison.reviewer_false_accepts == 0
    assert comparison.reviewer_false_rejects == 0
