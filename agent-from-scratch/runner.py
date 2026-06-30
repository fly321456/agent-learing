import json

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
            input_items.extend(response.output)

            tool_called = False
            for item in response.output:
                if item.type != "function_call":
                    continue

                arguments = json.loads(item.arguments)
                result = self.execute_tool(item.name, arguments)
                input_items.append(
                    {
                        "type": "function_call_output",
                        "call_id": item.call_id,
                        "output": str(result),
                    }
                )
                tool_called = True

            if not tool_called:
                print(response.output_text)
                return response.output_text
