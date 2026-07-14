from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .schemas import ToolCall, ToolResult


ToolHandler = Callable[..., str]


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]
    handler: ToolHandler

    def as_schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }


class ToolManager:
    def __init__(self, tools: list[ToolSpec]):
        self._tools = {tool.name: tool for tool in tools}
        if len(self._tools) != len(tools):
            raise ValueError("Tool names must be unique")

    @property
    def schemas(self) -> list[dict[str, Any]]:
        return [tool.as_schema() for tool in self._tools.values()]

    def execute(self, call: ToolCall) -> ToolResult:
        tool = self._tools.get(call.name)
        if tool is None:
            return ToolResult(call.id, call.name, "error", error=f"Unknown tool: {call.name}")
        try:
            output = tool.handler(**call.arguments)
        except Exception as exc:
            return ToolResult(call.id, call.name, "error", error=str(exc))
        return ToolResult(call.id, call.name, "success", output=str(output))
