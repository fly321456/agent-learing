from datetime import datetime


first_response = {
    "type": "function_call",
    "call_id": "call-1",
    "name": "get_current_time",
    "arguments": {},
}
print(f"function_call: {first_response['name']}")

tool_output = {
    "type": "function_call_output",
    "call_id": first_response["call_id"],
    "output": datetime.now().isoformat(timespec="seconds"),
}
assert tool_output["call_id"] == first_response["call_id"]
print("final: current time received")

