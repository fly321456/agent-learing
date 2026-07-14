from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Callable, TypeVar


T = TypeVar("T")


class RuntimeFailure(Exception):
    pass


class RetryableError(RuntimeFailure):
    pass


class DeterministicError(RuntimeFailure):
    pass


@dataclass(frozen=True)
class RetryPolicy:
    attempts: int = 1
    base_delay: float = 0.25

    def __post_init__(self) -> None:
        if self.attempts < 1:
            raise ValueError("attempts must be at least 1")
        if self.base_delay < 0:
            raise ValueError("base_delay cannot be negative")

    def run(
        self,
        operation: Callable[[], T],
        event_sink: Callable[[dict], None] | None = None,
    ) -> T:
        for attempt in range(1, self.attempts + 1):
            try:
                return operation()
            except RetryableError as exc:
                if attempt >= self.attempts:
                    raise
                if event_sink is not None:
                    event_sink({"type": "retry", "attempt": attempt, "error": str(exc)})
                delay = self.base_delay * (2 ** (attempt - 1))
                if delay:
                    time.sleep(delay)
        raise RuntimeError("retry loop ended unexpectedly")
