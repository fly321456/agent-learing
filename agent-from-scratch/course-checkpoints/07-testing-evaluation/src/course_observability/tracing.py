from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Event:
    type: str
    sequence: int
    run_id: str
    step: int
    data: dict[str, Any] = field(default_factory=dict)


def validate_event_contract(events: list[Event]) -> None:
    if not events:
        raise ValueError("event stream cannot be empty")
    expected = list(range(1, len(events) + 1))
    if [event.sequence for event in events] != expected:
        raise ValueError("event sequence must be continuous from 1")
    if len({event.run_id for event in events}) != 1:
        raise ValueError("all events must share one run_id")


class JsonlTraceWriter:
    def __init__(self, path: Path):
        self.path = Path(path)

    def __call__(self, event: Event) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(asdict(event), ensure_ascii=False) + "\n")
