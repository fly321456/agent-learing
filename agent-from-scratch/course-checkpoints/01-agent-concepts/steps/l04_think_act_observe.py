from __future__ import annotations

from pathlib import Path
import sys


CHECKPOINT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CHECKPOINT))

from agent_core import ScriptedLLM, run_agent  # noqa: E402


REPOSITORY = {
    "main.py": "def main(): print('hello')",
    "tests/test_main.py": "def test_main(): assert True",
}


def read_file(path: str) -> str:
    if path not in REPOSITORY:
        raise FileNotFoundError(path)
    return REPOSITORY[path]


def list_files() -> list[str]:
    return sorted(REPOSITORY)


def print_trace(task: str, result: dict) -> None:
    print(f"Task: {task}")
    for item in result["trace"]:
        print(f"Step {item['step']} Decision: {item['decision']}")
        if "action" in item:
            print(f"Step {item['step']} Action: {item['action']}")
        if "observation" in item:
            print(f"Step {item['step']} Observation: {item['observation']}")
        if "finish" in item:
            print(f"Step {item['step']} Finish: {item['finish']}")
    print(f"finish_reason: {result['finish_reason']}")


if __name__ == "__main__":
    task = "Find the project entry point even when README.md is missing"
    llm = ScriptedLLM(
        [
            {"type": "tool", "name": "read_file", "arguments": {"path": "README.md"}},
            {"type": "tool", "name": "list_files", "arguments": {}},
            {"type": "finish", "answer": "main.py is the likely entry point."},
        ]
    )
    result = run_agent(
        task,
        llm,
        tools={"read_file": read_file, "list_files": list_files},
        max_steps=5,
    )
    print_trace(task, result)

