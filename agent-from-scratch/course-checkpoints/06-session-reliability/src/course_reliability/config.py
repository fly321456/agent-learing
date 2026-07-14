from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class RuntimeConfig:
    max_steps: int = 8
    context_chars: int = 40_000
    retry_attempts: int = 2

    def __post_init__(self) -> None:
        if self.max_steps < 1:
            raise ValueError("max_steps must be positive")
        if self.context_chars < 1:
            raise ValueError("context_chars must be positive")
        if self.retry_attempts < 1:
            raise ValueError("retry_attempts must be positive")

    @classmethod
    def from_mapping(cls, values: Mapping[str, str]) -> "RuntimeConfig":
        try:
            return cls(
                max_steps=int(values.get("AGENT_MAX_STEPS", "8")),
                context_chars=int(values.get("AGENT_CONTEXT_CHARS", "40000")),
                retry_attempts=int(values.get("AGENT_RETRY_ATTEMPTS", "2")),
            )
        except ValueError as exc:
            if "must be" in str(exc):
                raise
            raise ValueError(f"Runtime config must contain integers: {exc}") from exc
