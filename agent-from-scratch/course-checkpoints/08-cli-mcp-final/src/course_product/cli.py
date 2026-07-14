from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(frozen=True)
class Event:
    type: str
    sequence: int
    run_id: str
    step: int
    data: dict[str, Any] = field(default_factory=dict)


def format_event(event: Event) -> str | None:
    if event.type == "tool_called":
        return f"[{event.step}] tool -> {event.data['name']}"
    if event.type == "tool_completed":
        return f"[{event.step}] tool <- {event.data['name']} ({event.data['status']})"
    if event.type == "llm_retry":
        return f"[{event.step}] model retry {event.data['attempt']}"
    return None


def request_approval(
    tool_name: str,
    arguments: dict[str, Any],
    input_fn: Callable[[str], str] = input,
) -> bool:
    prompt = f"Allow {tool_name} with {arguments}? [y/N] "
    return input_fn(prompt).strip().lower() in {"y", "yes"}
