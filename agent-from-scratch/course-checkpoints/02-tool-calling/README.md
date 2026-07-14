# 02 Tool Calling

This checkpoint demonstrates the Responses API request shape and one fixed two-call tool round trip without network access.

```powershell
python demo.py
python steps/l05_messages_instructions_context.py
python steps/l06_first_responses_text_call.py
python steps/l07_tool_schema_and_function_call.py
python steps/l08_execute_and_return_tool_output.py
```

Expected final demo lines include `requests=2`, the original `call_id`, and a final text answer. Online L06 is optional and runs only with `--online`, `OPENAI_API_KEY`, and `OPENAI_MODEL`.
