from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys


CHECKPOINT = Path(__file__).resolve().parents[1] / "course-checkpoints" / "07-testing-evaluation"
PACKAGE_ROOT = CHECKPOINT / "src"


def load_observability():
    sys.path.insert(0, str(PACKAGE_ROOT))
    try:
        import course_observability

        return course_observability
    finally:
        sys.path.pop(0)


def test_fake_llm_returns_scripted_responses_and_records_requests() -> None:
    module = load_observability()
    fake = module.FakeLLM([{"content": "first"}, {"content": "second"}])

    assert fake.generate([{"role": "user", "content": "one"}])["content"] == "first"
    assert fake.generate([{"role": "user", "content": "two"}])["content"] == "second"
    assert len(fake.requests) == 2
    assert fake.requests[1]["messages"][-1]["content"] == "two"


def test_event_contract_requires_one_run_and_continuous_sequence() -> None:
    module = load_observability()
    events = [
        module.Event("run_started", 1, "run-1", 0, {}),
        module.Event("run_completed", 2, "run-1", 1, {"finish_reason": "completed"}),
    ]
    module.validate_event_contract(events)

    try:
        module.validate_event_contract([
            events[0], module.Event("run_completed", 3, "run-2", 1, {})
        ])
    except ValueError as exc:
        assert "sequence" in str(exc) or "run_id" in str(exc)
    else:
        raise AssertionError("invalid event stream was accepted")


def test_temp_git_repository_e2e_reads_searches_patches_and_tests(tmp_path: Path) -> None:
    module = load_observability()
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / "app.py").write_text("value = 1\n", encoding="utf-8")
    (tmp_path / "test_app.py").write_text(
        "from app import value\n\ndef test_value():\n    assert value == 2\n", encoding="utf-8"
    )

    result = module.run_repository_e2e(tmp_path)

    assert result.passed is True
    assert result.actions == ["read", "search", "patch", "test"]
    assert (tmp_path / "app.py").read_text(encoding="utf-8") == "value = 2\n"


def test_twenty_case_metrics_are_computed_from_results() -> None:
    module = load_observability()
    cases = module.load_cases(CHECKPOINT / "cases.json")
    assert len(cases) == 20

    perfect = module.evaluate_cases(cases, lambda case: list(case.expected_tools))
    degraded = module.evaluate_cases(
        cases,
        lambda case: [] if case.id == cases[0].id else list(case.expected_tools),
    )

    assert perfect.total == perfect.passed == 20
    assert perfect.success_rate == 1.0
    assert perfect.tool_calls == 25
    assert degraded.passed == 19
    assert degraded.success_rate == 0.95
    assert degraded.failures == {"tool_sequence": 1}


def test_jsonl_trace_contains_each_event_in_order(tmp_path: Path) -> None:
    module = load_observability()
    trace = tmp_path / "trace.jsonl"
    writer = module.JsonlTraceWriter(trace)
    events = [
        module.Event("run_started", 1, "run-1", 0, {}),
        module.Event("tool_completed", 2, "run-1", 1, {"status": "success"}),
        module.Event("run_completed", 3, "run-1", 1, {"finish_reason": "completed"}),
    ]
    for event in events:
        writer(event)

    records = [json.loads(line) for line in trace.read_text(encoding="utf-8").splitlines()]
    assert [record["sequence"] for record in records] == [1, 2, 3]
    assert [record["type"] for record in records] == [event.type for event in events]


def test_module_seven_steps_and_demo_run() -> None:
    scripts = sorted((CHECKPOINT / "steps").glob("l*.py"))
    assert [path.name[:3] for path in scripts] == ["l25", "l26", "l27", "l28"]
    for script in scripts + [CHECKPOINT / "demo.py"]:
        completed = subprocess.run(
            [sys.executable, str(script)], cwd=script.parent, capture_output=True,
            text=True, encoding="utf-8", errors="strict", timeout=20, check=False,
        )
        assert completed.returncode == 0, completed.stderr
        assert completed.stdout.strip()


def test_module_seven_lessons_have_textbook_structure() -> None:
    repository = Path(__file__).resolve().parents[2]
    courses = next(path for path in repository.iterdir() if path.is_dir() and any(
        child.name.endswith("-Coding-Agent") for child in path.iterdir()
    ))
    main = next(path for path in courses.iterdir() if path.name.endswith("-Coding-Agent"))
    module = next(path for path in main.iterdir() if re.search(r"07-", path.name))
    lessons = sorted(path for path in module.glob("L*.md") if path.name[:3] in {
        "L25", "L26", "L27", "L28"
    })
    assert len(lessons) == 4
    for lesson in lessons:
        content = lesson.read_text(encoding="utf-8", errors="strict")
        assert 3_500 <= len(content) <= 15_000, lesson.name
        assert all(re.search(fr"^## {index}\.", content, re.MULTILINE) for index in range(1, 13))
        assert content.count("```") >= 6
        assert content.count("\uff1f") >= 5
    marker = "\u53c2\u8003\u7b54\u6848"
    assert len([path for path in module.glob("*.md") if marker in path.name]) == 1
