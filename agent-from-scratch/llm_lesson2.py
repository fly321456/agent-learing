from abc import ABC, abstractmethod
import os

from openai import OpenAI


class BaseLLM(ABC):
    @abstractmethod
    def generate(self, messages, tools=None):
        raise NotImplementedError


class OpenAILLM(BaseLLM):
    def __init__(self, api_key=None, model="gpt-5"):
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = model

    def generate(self, messages, tools=None):
        return self.client.responses.create(
            model=self.model,
            input=messages,
            tools=tools or [],
        )
