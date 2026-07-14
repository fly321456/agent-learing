from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys
from typing import Any, Iterable


class FakeLLM:
    def __init__(self, responses: Iterable[dict[str, Any]]):
        self._responses = list(responses)
        if not self._responses:
            raise ValueError("FakeLLM requires at least one response")
        self._index = 0
        self.requests: list[dict[str, Any]] = []

    def generate(self, messages, tools=None) -> dict[str, Any]:
        self.requests.append({"messages": list(messages), "tools": list(tools or [])})
        if self._index >= len(self._responses):
            raise RuntimeError("FakeLLM has no response left")
        response = self._responses[self._index]
        self._index += 1
        return response


@dataclass(frozen=True)
class E2EResult:
    passed: bool
    actions: list[str]
    test_output: str


def run_repository_e2e(workspace: Path) -> E2EResult:
    workspace = Path(workspace).resolve()
    if not (workspace / ".git").is_dir():
        raise ValueError("E2E workspace must be a Git repository")
    actions: list[str] = []

    source = workspace / "app.py"
    text = source.read_text(encoding="utf-8", errors="strict")
    actions.append("read")

    matches = [line for line in text.splitlines() if "value = 1" in line]
    if len(matches) != 1:
        return E2EResult(False, actions + ["search"], "expected one search match")
    actions.append("search")

    if text.count("value = 1") != 1:
        return E2EResult(False, actions, "patch target was not unique")
    source.write_text(text.replace("value = 1", "value = 2", 1), encoding="utf-8", newline="")
    actions.append("patch")

    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        cwd=workspace,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=20,
        check=False,
    )
    actions.append("test")
    output = completed.stdout + completed.stderr
    return E2EResult(completed.returncode == 0, actions, output)
