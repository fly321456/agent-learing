from __future__ import annotations

from pathlib import Path
import sys


CHECKPOINT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CHECKPOINT))

from responses_core import (  # noqa: E402
    ResponseItem,
    ScriptedResponse,
    ScriptedResponsesClient,
    run_fixed_tool_round_trip,
)


def get_current_time() -> str:
    return "2026-07-14T09:30:00+08:00"


if __name__ == "__main__":
    client = ScriptedResponsesClient(
        [
            ScriptedResponse(
                output=[ResponseItem("function_call", "call-08", "get_current_time", "{}")]
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
    output = result["tool_outputs"][0]
    print(f"function_call_output: call_id={output['call_id']} output={output['output']}")
    print(f"final: {result['answer']}")

