from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from typing import Any

from .schemas import Event, ToolResult


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
        newline="\n",
    )
    temporary.replace(path)


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if hasattr(value, "model_dump"):
        return _jsonable(value.model_dump())
    if hasattr(value, "to_dict"):
        return _jsonable(value.to_dict())
    return str(value)


@dataclass
class Session:
    id: str
    messages: list[dict[str, str]] = field(default_factory=list)

    def append(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})


class SessionStore:
    def __init__(self, directory: Path):
        self.directory = Path(directory)

    def save(self, session: Session) -> None:
        _write_json(self.directory / f"{session.id}.json", asdict(session))

    def load(self, session_id: str) -> Session:
        data = json.loads(
            (self.directory / f"{session_id}.json").read_text(encoding="utf-8")
        )
        return Session(id=data["id"], messages=data["messages"])


@dataclass(frozen=True)
class ContextWindow:
    max_chars: int = 40_000

    def __post_init__(self) -> None:
        if self.max_chars < 1:
            raise ValueError("max_chars must be positive")

    def trim(self, messages: list[dict[str, str]]) -> list[dict[str, str]]:
        used = 0
        kept: list[dict[str, str]] = []
        for message in reversed(messages):
            size = len(message.get("content", ""))
            if kept and used + size > self.max_chars:
                break
            kept.append(message)
            used += size
        kept.reverse()
        if len(kept) < len(messages):
            kept.insert(
                0,
                {
                    "role": "system",
                    "content": "[Earlier session messages were truncated by the context window.]",
                },
            )
        return kept


@dataclass
class RunCheckpoint:
    run_id: str
    user_input: str
    input_items: list[Any]
    events: list[Event]
    tool_results: list[ToolResult]
    next_step: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "user_input": self.user_input,
            "input_items": _jsonable(self.input_items),
            "events": [event.to_dict() for event in self.events],
            "tool_results": [asdict(result) for result in self.tool_results],
            "next_step": self.next_step,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RunCheckpoint":
        return cls(
            run_id=data["run_id"],
            user_input=data["user_input"],
            input_items=data["input_items"],
            events=[Event(**event) for event in data["events"]],
            tool_results=[ToolResult(**result) for result in data["tool_results"]],
            next_step=data["next_step"],
        )


class CheckpointStore:
    def __init__(self, directory: Path):
        self.directory = Path(directory)

    def save(self, checkpoint: RunCheckpoint) -> None:
        _write_json(self.directory / f"{checkpoint.run_id}.json", checkpoint.to_dict())

    def load(self, run_id: str) -> RunCheckpoint:
        data = json.loads(
            (self.directory / f"{run_id}.json").read_text(encoding="utf-8")
        )
        return RunCheckpoint.from_dict(data)

