from agent_loop import ModelResponse, ScriptedModel, ToolCall, run_agent

if __name__ == "__main__":
    calls = [ToolCall("calc", "calculator", {"expression": "6 * 7"}), ToolCall("clock", "time", {})]
    model = ScriptedModel([ModelResponse(tool_calls=calls), ModelResponse("The answer is 42 at 12:00.")])
    result = run_agent("calculate and tell time", model,
                       {"calculator": lambda expression: "42", "time": lambda: "12:00"})
    print(f"tool_results={len(result['tool_results'])}")
    print(f"finish_reason={result['finish_reason']} answer={result['answer']}")
