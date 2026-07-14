from __future__ import annotations

from collections.abc import Callable
from typing import Any


REPOSITORY = {
    "README.md": "A command-line todo application.",
    "todo.py": "def add_todo(title): ...",
}


def list_files() -> list[str]:
    return sorted(REPOSITORY)


def read_file(path: str) -> str:
    return REPOSITORY[path]


TOOLS: dict[str, Callable[..., Any]] = {
    "list_files": list_files,
    "read_file": read_file,
}


class ScriptedLLM:
    def __init__(self) -> None:
        self.round = 0

    def decide(self, task: str, observations: list[dict[str, Any]]) -> dict[str, Any]:
        del task, observations
        decisions = [
            {"type": "tool", "name": "list_files", "arguments": {}},
            {"type": "tool", "name": "read_file", "arguments": {"path": "README.md"}},
            {"type": "finish", "answer": "This is a command-line todo application."},
        ]
        decision = decisions[self.round]
        self.round += 1
        return decision


def run_agent(task: str, llm: ScriptedLLM, max_steps: int = 5) -> list[dict[str, Any]]:
    observations: list[dict[str, Any]] = []
    for step in range(1, max_steps + 1):
        decision = llm.decide(task, observations)
        print(f"Step {step} decision: {decision}")
        if decision["type"] == "finish":
            print(f"Finish: {decision['answer']}")
            return observations

        tool = TOOLS[decision["name"]]
        output = tool(**decision["arguments"])
        observation = {"tool": decision["name"], "output": output}
        observations.append(observation)
        print(f"Step {step} observation: {observation}")
    return observations


if __name__ == "__main__":
    print("LLM + Tool + Loop + Environment")
    run_agent("Explain this repository", ScriptedLLM())

