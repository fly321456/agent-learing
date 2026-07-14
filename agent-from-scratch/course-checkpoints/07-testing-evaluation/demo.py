from pathlib import Path
import json
import sys
import tempfile


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
from course_observability import (  # noqa: E402
    Event, JsonlTraceWriter, evaluate_cases, load_cases, validate_event_contract,
)


def main() -> None:
    cases = load_cases(ROOT / "cases.json")
    metrics = evaluate_cases(cases, lambda case: list(case.expected_tools))
    events = [Event("run_started", 1, "eval-1", 0), Event("run_completed", 2, "eval-1", 1)]
    validate_event_contract(events)
    with tempfile.TemporaryDirectory() as directory:
        trace = Path(directory) / "eval.jsonl"
        writer = JsonlTraceWriter(trace)
        for event in events:
            writer(event)
        lines = [json.loads(line) for line in trace.read_text(encoding="utf-8").splitlines()]
    print(
        f"total={metrics.total} passed={metrics.passed} tool_calls={metrics.tool_calls} "
        f"steps={metrics.steps} trace_events={len(lines)}"
    )


if __name__ == "__main__":
    main()
