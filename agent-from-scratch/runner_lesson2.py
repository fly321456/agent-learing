class Runner:
    def run(self, agent, user_input):
        messages = [
            {
                "role": "system",
                "content": agent.instructions,
            },
            {
                "role": "user",
                "content": user_input,
            },
        ]

        response = agent.llm.generate(messages, tools=agent.tools)
        print(response.output_text)
