from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class RuntimeConfig:
    model: str | None
    max_steps: int
    workspace: Path
    command_timeout: float
    retry_attempts: int
    context_chars: int

    @classmethod
    def from_env(cls) -> "RuntimeConfig":
        return cls(
            model=os.getenv("OPENAI_MODEL"),
            max_steps=int(os.getenv("AGENT_MAX_STEPS", "8")),
            workspace=Path(os.getenv("AGENT_WORKSPACE", ".")).resolve(),
            command_timeout=float(os.getenv("AGENT_COMMAND_TIMEOUT", "30")),
            retry_attempts=int(os.getenv("AGENT_RETRY_ATTEMPTS", "2")),
            context_chars=int(os.getenv("AGENT_CONTEXT_CHARS", "40000")),
        )
