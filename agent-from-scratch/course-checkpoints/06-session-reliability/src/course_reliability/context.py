from __future__ import annotations

from dataclasses import dataclass

from .session import Message


@dataclass(frozen=True)
class ContextResult:
    messages: list[Message]
    truncated: bool
    used_chars: int


@dataclass(frozen=True)
class ContextWindow:
    max_chars: int

    def __post_init__(self) -> None:
        if self.max_chars < 1:
            raise ValueError("max_chars must be positive")

    def build(self, messages: list[Message], summary: str | None = None) -> ContextResult:
        used = 0
        kept: list[Message] = []
        for message in reversed(messages):
            size = len(message.content)
            if kept and used + size > self.max_chars:
                break
            if not kept and size > self.max_chars:
                kept.append(message)
                used += size
                break
            kept.append(message)
            used += size
        kept.reverse()
        truncated = len(kept) < len(messages)
        if truncated:
            marker = summary or "Earlier session messages were truncated."
            kept.insert(0, Message("system", f"[Context summary] {marker}", "context"))
        return ContextResult(kept, truncated, used)
