from __future__ import annotations

from typing import Any


def workflow(repository: dict[str, str]) -> str:
    """The developer fixes the path before execution starts."""
    readme = repository["README.md"]
    source_count = sum(name.endswith(".py") for name in repository)
    return f"{readme} Python files: {source_count}."


class RepositoryAgent:
    def decide(self, observations: list[dict[str, Any]]) -> dict[str, Any]:
        if not observations:
            return {"type": "read", "path": "README.md"}
        if observations[-1]["status"] == "missing":
            return {"type": "list"}
        if observations[-1]["action"] == "read":
            return {"type": "finish", "answer": observations[-1]["content"]}
        files = observations[-1]["files"]
        return {"type": "finish", "answer": f"No README. Files: {', '.join(files)}"}


def agent(repository: dict[str, str]) -> str:
    observations: list[dict[str, Any]] = []
    brain = RepositoryAgent()
    while True:
        decision = brain.decide(observations)
        print(f"  decision: {decision}")
        if decision["type"] == "finish":
            return decision["answer"]
        if decision["type"] == "read":
            path = decision["path"]
            if path in repository:
                observation = {"action": "read", "status": "success", "content": repository[path]}
            else:
                observation = {"action": "read", "status": "missing", "path": path}
        else:
            observation = {"action": "list", "status": "success", "files": sorted(repository)}
        observations.append(observation)
        print(f"  observation: {observation}")


if __name__ == "__main__":
    with_readme = {"README.md": "A weather CLI.", "weather.py": "..."}
    without_readme = {"main.py": "...", "tests.py": "..."}

    print("Workflow with README:", workflow(with_readme))
    try:
        print("Workflow without README:", workflow(without_readme))
    except KeyError as error:
        print(f"Workflow without README failed: {error}")

    print("Agent with README:")
    print(" ", agent(with_readme))
    print("Agent without README:")
    print(" ", agent(without_readme))

