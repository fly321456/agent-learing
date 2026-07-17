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
            output_items = list(raw_response.output or [])
            tool_calls: list[ToolCall] = []
            refusals: list[str] = []
            for item in output_items:
                if item.type == "function_call":
                    arguments = json.loads(item.arguments)
                    if not isinstance(arguments, dict):
                        raise TypeError("Function arguments must decode to a JSON object")
                    tool_calls.append(
                        ToolCall(
                            id=item.call_id,
                            name=item.name,
                            arguments=arguments,
                        )
                    )
                elif item.type == "message":
                    refusals.extend(
                        content.refusal
                        for content in item.content
                        if content.type == "refusal"
                    )
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

        status = raw_response.status or "completed"
        if status in {"queued", "in_progress"}:
            raise LLMError(
                f"OpenAI synchronous response returned non-terminal status: {status}"
            )
        if status not in {"completed", "incomplete", "failed", "cancelled"}:
            raise LLMError(f"OpenAI response returned unknown status: {status}")

        content = raw_response.output_text or ""
        refusal = "\n".join(refusals)
        status_detail = None
        if status == "incomplete" and raw_response.incomplete_details is not None:
            status_detail = raw_response.incomplete_details.reason
        elif status == "failed" and raw_response.error is not None:
            status_detail = f"{raw_response.error.code}: {raw_response.error.message}"
        elif refusal:
            content = content or refusal
            status_detail = refusal

        if status != "completed":
            finish_reason = status
        elif refusal:
            finish_reason = "refusal"
        elif tool_calls:
            finish_reason = "tool_calls"
        else:
            finish_reason = "completed"

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            continuation_items=output_items,
            finish_reason=finish_reason,
            status_detail=status_detail,
            raw_response=raw_response,
        )
