from __future__ import annotations

from dataclasses import dataclass, field
import json
from typing import Any, Callable, Iterable


@dataclass
class ResponseItem:
    type: str
    call_id: str = ""
    name: str = ""
    arguments: str = "{}"


@dataclass
class ScriptedResponse:
    output_text: str = ""
    output: list[ResponseItem] = field(default_factory=list)


class ScriptedResponsesClient:
    """A deterministic stand-in for client.responses used by the course."""

    def __init__(self, responses: Iterable[ScriptedResponse]) -> None:
        self._responses = list(responses)
        self._index = 0
        self.requests: list[dict[str, Any]] = []

    def create(self, **request: Any) -> ScriptedResponse:
        self.requests.append(request)
        if self._index >= len(self._responses):
            raise RuntimeError("ScriptedResponsesClient has no response left")
        response = self._responses[self._index]
        self._index += 1
        return response


def generate_text(
    client: Any,
    model: str,
    instructions: str,
    user_input: str,
) -> str:
    response = client.create(
        model=model,
        instructions=instructions,
        input=user_input,
    )
    return response.output_text


def time_tool_schema() -> dict[str, Any]:
    return {
        "type": "function",
        "name": "get_current_time",
        "description": "Return a deterministic local time for the teaching example.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
        "strict": True,
    }


def run_fixed_tool_round_trip(
    client: Any,
    *,
    model: str,
    user_input: str,
    tool_handlers: dict[str, Callable[..., str]],
) -> dict[str, Any]:
    """Perform exactly two model calls; Module 3 will replace this with a loop."""
    input_items: list[Any] = [{"role": "user", "content": user_input}]
    first = client.create(model=model, input=input_items, tools=[time_tool_schema()])
    input_items.extend(first.output)
    tool_outputs: list[dict[str, str]] = []

    for item in first.output:
        if item.type != "function_call":
            continue
        try:
            arguments = json.loads(item.arguments)
            if not isinstance(arguments, dict):
                raise ValueError("arguments must decode to an object")
            handler = tool_handlers[item.name]
            output = str(handler(**arguments))
        except json.JSONDecodeError as error:
            output = f"error: invalid JSON arguments: {error.msg}"
        except KeyError:
            output = f"error: unknown tool: {item.name}"
        except Exception as error:
            output = f"error: tool execution failed: {error}"

        tool_output = {
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": output,
        }
        input_items.append(tool_output)
        tool_outputs.append(tool_output)

    second = client.create(model=model, input=input_items, tools=[time_tool_schema()])
    return {
        "answer": second.output_text,
        "input_items": input_items,
        "tool_outputs": tool_outputs,
    }

