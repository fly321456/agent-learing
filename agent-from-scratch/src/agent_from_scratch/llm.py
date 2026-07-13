from abc import ABC, abstractmethod
import json
import os
from typing import Any, Iterable

from .errors import LLMError, RetryableLLMError
from .schemas import LLMResponse, ToolCall


class BaseLLM(ABC):
    @abstractmethod
    def generate(
        self, messages: list[Any], tools: list[dict[str, Any]] | None = None
    ) -> LLMResponse:
        raise NotImplementedError


class FakeLLM(BaseLLM):
    def __init__(self, responses: Iterable[LLMResponse], repeat_last: bool = False):
        self._responses = list(responses)
        if not self._responses:
            raise ValueError("FakeLLM requires at least one response")
        self._index = 0
        self._repeat_last = repeat_last
        self.requests: list[dict[str, Any]] = []

    def generate(self, messages, tools=None) -> LLMResponse:
        self.requests.append({"messages": list(messages), "tools": list(tools or [])})
        if self._index >= len(self._responses):
            if not self._repeat_last:
                raise LLMError("FakeLLM has no response left")
            return self._responses[-1]
        response = self._responses[self._index]
        self._index += 1
        return response


class OpenAILLM(BaseLLM):
    def __init__(self, api_key: str | None = None, model: str | None = None):
        selected_model = model or os.getenv("OPENAI_MODEL")
        if not selected_model:
            raise LLMError("Provide a model or set OPENAI_MODEL")
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise LLMError("Install the 'openai' package to use OpenAILLM") from exc
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = selected_model

    def generate(self, messages, tools=None) -> LLMResponse:
        try:
            raw_response = self.client.responses.create(
                model=self.model,
                input=messages,
                tools=tools or [],
            )
            tool_calls = [
                ToolCall(
                    id=item.call_id,
                    name=item.name,
                    arguments=json.loads(item.arguments),
                )
                for item in raw_response.output
                if item.type == "function_call"
            ]
        except (TypeError, ValueError) as exc:
            raise LLMError(f"Invalid OpenAI response: {exc}") from exc
        except Exception as exc:
            error_type = type(exc).__name__
            status_code = getattr(exc, "status_code", None)
            retryable = error_type in {
                "APIConnectionError",
                "APITimeoutError",
                "InternalServerError",
                "RateLimitError",
            } or status_code == 429 or (
                isinstance(status_code, int) and status_code >= 500
            )
            error = RetryableLLMError if retryable else LLMError
            raise error(f"OpenAI request failed: {exc}") from exc

        return LLMResponse(
            content=raw_response.output_text or "",
            tool_calls=tool_calls,
            continuation_items=list(raw_response.output),
            finish_reason="tool_calls" if tool_calls else "completed",
            raw_response=raw_response,
        )
