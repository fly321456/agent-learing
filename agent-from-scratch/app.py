from agent import Agent
from runner import Runner


def main():
    agent = Agent(
        model="gpt-5",
        instructions="You are a helpful coding agent.",
        tools=[],
    )

    runner = Runner()
    runner.run(agent, "Hello, agent.")


if __name__ == "__main__":
    main()
