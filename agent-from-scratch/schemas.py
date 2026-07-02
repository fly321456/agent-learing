from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class Event:
    type: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class Block:
    type: str
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    events: list[Event] = field(default_factory=list)
    blocks: list[Block] = field(default_factory=list)
    finish_reason: str | None = None
    raw_response: Any | None = None


TIME_TOOL_SCHEMA = {
    "type": "function",
    "name": "get_current_time",
    "description": "Get the current local time when the user asks for the current time, date, or now.",
    "parameters": {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False,
    },
}

ALL_TOOL_SCHEMAS = [TIME_TOOL_SCHEMA]