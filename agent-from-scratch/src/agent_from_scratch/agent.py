from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .llm import BaseLLM
    from .tools import ToolSpec


@dataclass(frozen=True)
class Agent:
    name: str
    instructions: str
    llm: "BaseLLM"
    tools: list["ToolSpec"] = field(default_factory=list)
    max_steps: int = 8

    def __post_init__(self) -> None:
        if self.max_steps < 1:
            raise ValueError("max_steps must be at least 1")

