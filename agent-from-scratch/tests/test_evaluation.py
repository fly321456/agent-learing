import json
from importlib.resources import files
from pathlib import Path

from agent_from_scratch.evaluation import (
    load_cases,
    run_offline_protocol_eval,
    summarize_results,
)


def test_eval_catalog_contains_twenty_unique_coding_agent_cases():
    cases = load_cases()

    assert len(cases) == 20
    assert len({case.id for case in cases}) == 20
    assert {case.category for case in cases} >= {
        "read",
        "search",
        "edit",
        "execute",
        "safety",
    }


def test_eval_catalog_is_packaged_with_the_runtime():
    catalog = files("agent_from_scratch").joinpath("data", "cases.json")

    assert catalog.is_file()
    project_catalog = Path(__file__).resolve().parents[1] / "evals" / "cases.json"
    assert json.loads(catalog.read_text(encoding="utf-8")) == json.loads(
        project_catalog.read_text(encoding="utf-8")
    )


def test_eval_summary_records_core_metrics():
    summary = summarize_results(
        [
            {"passed": True, "tool_calls": 1, "steps": 2, "duration_ms": 10, "failure": None},
            {"passed": False, "tool_calls": 2, "steps": 3, "duration_ms": 20, "failure": "timeout"},
        ]
    )

    assert summary == {
        "total": 2,
        "passed": 1,
        "success_rate": 0.5,
        "tool_calls": 3,
        "steps": 5,
        "duration_ms": 30,
        "failures": {"timeout": 1},
    }


def test_offline_protocol_eval_runs_all_twenty_tool_sequences():
    summary = run_offline_protocol_eval(load_cases())

    assert summary["total"] == 20
    assert summary["passed"] == 20
    assert summary["success_rate"] == 1.0
    assert summary["tool_calls"] == 25
    assert summary["steps"] == 40
    assert summary["failures"] == {}
