from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Iterable

from .schemas import LLMResponse


class BaseLLM(ABC):
    @abstractmethod
    def generate(
        self,
        messages: list[Any],
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        raise NotImplementedError


class ScriptedLLM(BaseLLM):
    """Deterministic model used by the course and its offline tests."""

    def __init__(self, responses: Iterable[LLMResponse], repeat_last: bool = False):
        self._responses = list(responses)
        if not self._responses:
            raise ValueError("ScriptedLLM requires at least one response")
        self._index = 0
        self._repeat_last = repeat_last
        self.requests: list[dict[str, Any]] = []

    def generate(self, messages, tools=None) -> LLMResponse:
        self.requests.append({"messages": list(messages), "tools": list(tools or [])})
        if self._index >= len(self._responses):
            if not self._repeat_last:
                raise RuntimeError("ScriptedLLM has no response left")
            return self._responses[-1]
        response = self._responses[self._index]
        self._index += 1
        return response
