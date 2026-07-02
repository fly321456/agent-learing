from schemas import Event
from tools import TOOL_REGISTRY


class Runner:
    def execute_tool(self, tool_name, arguments):
        tool = TOOL_REGISTRY.get(tool_name)
        if tool is None:
            return f"Tool not found: {tool_name}"

        return tool(**arguments)

    def run(self, agent, user_input):
        input_items = [
            {
                "role": "system",
                "content": agent.instructions,
            },
            {
                "role": "user",
                "content": user_input,
            },
        ]

        while True:
            response = agent.llm.generate(input_items, tools=agent.tools)
            input_items.extend(response.raw_response.output)

            if response.tool_calls:
                response.events.extend(
                    Event(
                        type="tool_call",
                        payload={
                            "tool_name": tool_call.name,
                            "arguments": tool_call.arguments,
                        },
                    )
                    for tool_call in response.tool_calls
                )

            tool_called = False
            for tool_call in response.tool_calls:
                result = self.execute_tool(tool_call.name, tool_call.arguments)
                response.events.append(
                    Event(
                        type="tool_result",
                        payload={
                            "tool_name": tool_call.name,
                            "result": str(result),
                        },
                    )
                )
                input_items.append(
                    {
                        "type": "function_call_output",
                        "call_id": tool_call.id,
                        "output": str(result),
                    }
                )
                tool_called = True

            if not tool_called:
                print(response.content)
                return response.content