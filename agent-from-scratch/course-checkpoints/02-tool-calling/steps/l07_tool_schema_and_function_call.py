from __future__ import annotations

from pathlib import Path
import sys


CHECKPOINT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CHECKPOINT))

from responses_core import ResponseItem, ScriptedResponse, ScriptedResponsesClient, time_tool_schema  # noqa: E402


if __name__ == "__main__":
    client = ScriptedResponsesClient(
        [
            ScriptedResponse(
                output=[
                    ResponseItem(
                        type="function_call",
                        call_id="call-07",
                        name="get_current_time",
                        arguments="{}",
                    )
                ]
            )
        ]
    )
    response = client.create(
        model="course-model",
        input="What time is it?",
        tools=[time_tool_schema()],
    )
    print(f"schema.strict: {time_tool_schema()['strict']}")
    for item in response.output:
        print(f"function_call: name={item.name} call_id={item.call_id} arguments={item.arguments}")
    print("tool_executed: false")

