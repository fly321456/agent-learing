from steps.l08_execute_and_return_tool_output import get_current_time
from responses_core import (
    ResponseItem,
    ScriptedResponse,
    ScriptedResponsesClient,
    run_fixed_tool_round_trip,
)


if __name__ == "__main__":
    client = ScriptedResponsesClient(
        [
            ScriptedResponse(
                output=[ResponseItem("function_call", "call-demo", "get_current_time", "{}")]
            ),
            ScriptedResponse(output_text="The current time is 09:30 in Asia/Shanghai."),
        ]
    )
    result = run_fixed_tool_round_trip(
        client,
        model="course-model",
        user_input="What time is it?",
        tool_handlers={"get_current_time": get_current_time},
    )
    print(f"requests={len(client.requests)}")
    print(f"call_id={result['tool_outputs'][0]['call_id']}")
    print(f"final={result['answer']}")
