from abc import ABC, abstractmethod
import json
import os

from openai import OpenAI

from schemas import LLMResponse, ToolCall


class BaseLLM(ABC):
    @abstractmethod
    def generate(self, messages, tools=None):
        raise NotImplementedError


class OpenAILLM(BaseLLM):
    def __init__(self, api_key=None, model="gpt-5"):
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = model

    def generate(self, messages, tools=None):
        raw_response = self.client.responses.create(
            model=self.model,
            input=messages,
            tools=tools or [],
        )
        tool_calls = []
        for item in raw_response.output:
            if item.type != "function_call":
                continue

            tool_calls.append(
                ToolCall(
                    id=item.call_id,
                    name=item.name,
                    arguments=json.loads(item.arguments),
                )
            )

        return LLMResponse(
            content=raw_response.output_text or "",
            tool_calls=tool_calls,
            raw_response=raw_response,
        )