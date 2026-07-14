from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from typing import Callable


@dataclass
class RunCheckpoint:
    run_id: str
    next_step: int
    completed_calls: dict[str, str] = field(default_factory=dict)


class CheckpointStore:
    def __init__(self, directory: Path):
        self.directory = Path(directory)

    def save(self, checkpoint: RunCheckpoint) -> None:
        path = self.directory / f"{checkpoint.run_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(asdict(checkpoint), ensure_ascii=False, indent=2),
            encoding="utf-8",
            newline="\n",
        )
        temporary.replace(path)

    def load(self, run_id: str) -> RunCheckpoint:
        data = json.loads(
            (self.directory / f"{run_id}.json").read_text(encoding="utf-8", errors="strict")
        )
        return RunCheckpoint(**data)


def execute_once(checkpoint: RunCheckpoint, call_id: str, operation: Callable[[], str]) -> str:
    if call_id in checkpoint.completed_calls:
        return checkpoint.completed_calls[call_id]
    output = operation()
    checkpoint.completed_calls[call_id] = output
    return output
