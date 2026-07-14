from __future__ import annotations


REPOSITORY = {
    "README.md": "A tiny calculator project.",
    "calculator.py": "def add(a, b): return a + b",
    "test_calculator.py": "def test_add(): assert add(1, 2) == 3",
}


def single_shot_answer(task: str) -> str:
    del task
    return "This repository probably contains Python source and tests."


def run_small_agent(task: str) -> list[str]:
    del task
    trace = ["Decision: inspect the file list"]
    files = sorted(REPOSITORY)
    trace.append(f"Observation: files = {files}")
    trace.append("Decision: read README.md")
    trace.append(f"Observation: {REPOSITORY['README.md']}")
    trace.append("Finish: this is a calculator project with one source file and one test file.")
    return trace


if __name__ == "__main__":
    task = "Explain this unfamiliar repository"
    print(f"Task: {task}")
    print(f"Single-shot: {single_shot_answer(task)}")
    print("Agent trace:")
    for line in run_small_agent(task):
        print(f"  {line}")

