from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
import re
from typing import Any
from uuid import uuid4

from .schemas import Event, ToolResult


_IDENTIFIER = re.compile(r"[A-Za-z0-9_-]{1,64}\Z")
_SCHEMA_VERSION = 1
_MAX_STATE_BYTES = 5_000_000


def _store_path(directory: Path, identifier: str) -> Path:
    if not isinstance(identifier, str) or _IDENTIFIER.fullmatch(identifier) is None:
        raise ValueError(
            "Store identifiers must use 1-64 ASCII letters, digits, '_' or '-'"
        )
    root = Path(directory).resolve()
    candidate = (root / f"{identifier}.json").resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError("Store identifier resolves outside its directory") from exc
    return candidate


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
        newline="\n",
    )
    temporary.replace(path)


def _read_json(path: Path) -> dict[str, Any]:
    if path.stat().st_size > _MAX_STATE_BYTES:
        raise ValueError(f"State file is too large: {path.name}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("State file must contain a JSON object")
    version = data.get("schema_version", _SCHEMA_VERSION)
    if version != _SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported state schema version {version!r}; expected {_SCHEMA_VERSION}"
        )
    return data


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


@dataclass(frozen=True)
class Message:
    role: str
    content: str
    turn_id: str


@dataclass(frozen=True)
class Turn:
    id: str
    user_input: str


@dataclass
class Session:
    id: str
    messages: list[Message] = field(default_factory=list)

    def start_turn(self, user_input: str) -> Turn:
        turn = Turn(str(uuid4()), user_input)
        self.messages.append(Message("user", user_input, turn.id))
        return turn

    def append_assistant(self, turn_id: str, content: str) -> None:
        if not any(message.turn_id == turn_id for message in self.messages):
            raise ValueError(f"Unknown turn_id: {turn_id}")
        self.messages.append(Message("assistant", content, turn_id))

    def append(self, role: str, content: str, turn_id: str | None = None) -> None:
        """Compatibility wrapper; new code should use the turn-aware methods."""
        if role == "user" and turn_id is None:
            self.start_turn(content)
            return
        if turn_id is None:
            turn_id = next(
                (
                    message.turn_id
                    for message in reversed(self.messages)
                    if message.role == "user"
                ),
                str(uuid4()),
            )
        if role == "assistant":
            self.append_assistant(turn_id, content)
            return
        self.messages.append(Message(role, content, turn_id))


class SessionStore:
    def __init__(self, directory: Path):
        self.directory = Path(directory)

    def save(self, session: Session) -> None:
        _write_json(
            _store_path(self.directory, session.id),
            {"schema_version": _SCHEMA_VERSION, **asdict(session)},
        )

    def exists(self, session_id: str) -> bool:
        return _store_path(self.directory, session_id).is_file()

    def load(self, session_id: str) -> Session:
        data = _read_json(_store_path(self.directory, session_id))
        messages: list[Message] = []
        legacy_turn_id: str | None = None
        for item in data["messages"]:
            turn_id = item.get("turn_id")
            if turn_id is None:
                if item["role"] == "user" or legacy_turn_id is None:
                    legacy_turn_id = str(uuid4())
                turn_id = legacy_turn_id
            messages.append(Message(item["role"], item["content"], turn_id))
        return Session(id=data["id"], messages=messages)


@dataclass(frozen=True)
class ContextResult:
    messages: list[Message]
    truncated: bool
    used_chars: int


@dataclass(frozen=True)
class ContextWindow:
    max_chars: int = 40_000

    def __post_init__(self) -> None:
        if self.max_chars < 1:
            raise ValueError("max_chars must be positive")

    def build(
        self, messages: list[Message], summary: str | None = None
    ) -> ContextResult:
        used = 0
        kept: list[Message] = []
        for message in reversed(messages):
            size = len(message.content)
            if not kept and size > self.max_chars:
                raise ValueError("A single message exceeds the context budget")
            if used + size > self.max_chars:
                break
            kept.append(message)
            used += size
        kept.reverse()
        truncated = len(kept) < len(messages)
        if truncated:
            marker_text = summary or "[truncated]"
            if len(marker_text) >= self.max_chars:
                marker_text = "[truncated]"
            while len(kept) > 1 and used + len(marker_text) > self.max_chars:
                used -= len(kept.pop(0).content)
            if used + len(marker_text) <= self.max_chars:
                kept.insert(0, Message("system", marker_text, "context"))
                used += len(marker_text)
        return ContextResult(kept, truncated, used)

    def trim(self, messages: list[Any]) -> list[dict[str, str]]:
        normalized = [
            message
            if isinstance(message, Message)
            else Message(
                message["role"],
                message.get("content", ""),
                message.get("turn_id", f"legacy-{index}"),
            )
            for index, message in enumerate(messages)
        ]
        return [
            {"role": message.role, "content": message.content}
            for message in self.build(normalized).messages
        ]


@dataclass
class RunCheckpoint:
    run_id: str
    user_input: str
    input_items: list[Any]
    events: list[Event]
    tool_results: list[ToolResult]
    next_step: int
    completed_calls: dict[str, ToolResult] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": _SCHEMA_VERSION,
            "run_id": self.run_id,
            "user_input": self.user_input,
            "input_items": _jsonable(self.input_items),
            "events": [event.to_dict() for event in self.events],
            "tool_results": [asdict(result) for result in self.tool_results],
            "next_step": self.next_step,
            "completed_calls": {
                call_id: asdict(result)
                for call_id, result in self.completed_calls.items()
            },
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
            completed_calls={
                call_id: ToolResult(**result)
                for call_id, result in data.get("completed_calls", {}).items()
            }
            or {
                result["call_id"]: ToolResult(**result)
                for result in data.get("tool_results", [])
            },
        )


class CheckpointStore:
    def __init__(self, directory: Path):
        self.directory = Path(directory)

    def save(self, checkpoint: RunCheckpoint) -> None:
        _write_json(
            _store_path(self.directory, checkpoint.run_id), checkpoint.to_dict()
        )

    def exists(self, run_id: str) -> bool:
        return _store_path(self.directory, run_id).is_file()

    def load(self, run_id: str) -> RunCheckpoint:
        data = _read_json(_store_path(self.directory, run_id))
        return RunCheckpoint.from_dict(data)
