TIME_TOOL_SCHEMA = {
    "type": "function",
    "name": "get_current_time",
    "description": "Get the current local time when the user asks for the current time, date, or now.",
    "parameters": {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False,
    },
}

ALL_TOOL_SCHEMAS = [TIME_TOOL_SCHEMA]
