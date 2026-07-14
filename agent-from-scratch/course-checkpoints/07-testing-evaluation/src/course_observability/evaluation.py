from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import time
from typing import Callable


@dataclass(frozen=True)
class EvalCase:
    id: str
    category: str
    prompt: str
    expected_tools: list[str]


@dataclass(frozen=True)
class EvalMetrics:
    total: int
    passed: int
    success_rate: float
    tool_calls: int
    steps: int
    duration_ms: float
    failures: dict[str, int]


def load_cases(path: Path) -> list[EvalCase]:
    data = json.loads(Path(path).read_text(encoding="utf-8", errors="strict"))
    cases = [EvalCase(**item) for item in data]
    if len({case.id for case in cases}) != len(cases):
        raise ValueError("Evaluation case ids must be unique")
    return cases


def evaluate_cases(
    cases: list[EvalCase],
    executor: Callable[[EvalCase], list[str]],
) -> EvalMetrics:
    passed = 0
    tool_calls = 0
    steps = 0
    failures: dict[str, int] = {}
    started = time.perf_counter()
    for case in cases:
        actual_tools = executor(case)
        tool_calls += len(actual_tools)
        steps += 2 if actual_tools else 1
        if actual_tools == case.expected_tools:
            passed += 1
        else:
            failures["tool_sequence"] = failures.get("tool_sequence", 0) + 1
    total = len(cases)
    return EvalMetrics(
        total=total,
        passed=passed,
        success_rate=passed / total if total else 0.0,
        tool_calls=tool_calls,
        steps=steps,
        duration_ms=(time.perf_counter() - started) * 1000,
        failures=failures,
    )
