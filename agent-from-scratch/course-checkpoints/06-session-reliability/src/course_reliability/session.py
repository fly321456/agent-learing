from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from uuid import uuid4


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


class SessionStore:
    def __init__(self, directory: Path):
        self.directory = Path(directory)

    def save(self, session: Session) -> None:
        path = self.directory / f"{session.id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(asdict(session), ensure_ascii=False, indent=2),
            encoding="utf-8",
            newline="\n",
        )
        temporary.replace(path)

    def load(self, session_id: str) -> Session:
        path = self.directory / f"{session_id}.json"
        data = json.loads(path.read_text(encoding="utf-8", errors="strict"))
        return Session(data["id"], [Message(**item) for item in data["messages"]])
