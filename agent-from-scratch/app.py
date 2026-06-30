from agent import Agent
from llm import OpenAILLM
from prompts import DEFAULT_SYSTEM_PROMPT
from runner import Runner
from schemas import ALL_TOOL_SCHEMAS


def main():
    llm = OpenAILLM()
    agent = Agent(
        llm=llm,
        instructions=DEFAULT_SYSTEM_PROMPT,
        tools=ALL_TOOL_SCHEMAS,
    )

    runner = Runner()
    runner.run(agent, "What time is it now?")


if __name__ == "__main__":
    main()
