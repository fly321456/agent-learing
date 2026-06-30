from agent_lesson2 import Agent
from llm_lesson2 import OpenAILLM
from runner_lesson2 import Runner


def main():
    llm = OpenAILLM()
    agent = Agent(
        llm=llm,
        instructions="你是一名助手。",
        tools=[],
    )

    runner = Runner()
    runner.run(agent, "你好，请介绍一下自己。")


if __name__ == "__main__":
    main()
