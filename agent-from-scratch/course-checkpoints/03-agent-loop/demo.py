from dataclasses import dataclass


@dataclass
class ToolCall:
    name: str
    arguments: dict


def calculator(expression: str) -> str:
    if expression != "6 * 7":
        raise ValueError("This teaching calculator only accepts 6 * 7")
    return "42"


def current_time() -> str:
    return "12:00:00"


tools = {"calculator": calculator, "current_time": current_time}
script = [
    [ToolCall("calculator", {"expression": "6 * 7"}), ToolCall("current_time", {})],
    "completed",
]
tool_results = []

for step in range(1, 4):
    response = script.pop(0)
    if response == "completed":
        print("finish_reason=completed")
        break
    for call in response:
        handler = tools.get(call.name)
        if handler is None:
            tool_results.append({"name": call.name, "status": "unknown_tool"})
            continue
        tool_results.append({"name": call.name, "status": "success", "output": handler(**call.arguments)})
else:
    print("finish_reason=max_steps")

print(f"tool_results={len(tool_results)}")

