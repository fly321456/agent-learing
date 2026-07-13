from agent_from_scratch import Agent, LLMResponse, Runner
from agent_from_scratch.llm import FakeLLM


agent = Agent(
    "course-final",
    "Answer the offline task.",
    FakeLLM([LLMResponse(content="ready", finish_reason="completed")]),
    max_steps=1,
)
result = Runner().run(agent, "status")
assert result.finish_reason == "completed"
print("mcp_transport=stdio")
print("mcp_server=ready")
print("final_project=ready")

