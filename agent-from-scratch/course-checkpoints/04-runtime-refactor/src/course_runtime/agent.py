from __future__ import annotations

from dataclasses import dataclass, field

from .llm import BaseLLM
from .tools import ToolSpec


@dataclass(frozen=True)
class Agent:
    """Static agent configuration; execution belongs to Runner."""

    name: str
    instructions: str
    llm: BaseLLM
    tools: list[ToolSpec] = field(default_factory=list)
    max_steps: int = 5

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Agent name cannot be empty")
        if self.max_steps < 1:
            raise ValueError("max_steps must be at least 1")
