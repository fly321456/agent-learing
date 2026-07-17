from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from openai.types.responses import (
    Response,
    ResponseFunctionToolCall,
    ResponseOutputMessage,
    ResponseOutputRefusal,
    ResponseOutputText,
)
from openai.types.responses.response import IncompleteDetails
from openai.types.responses.response_error import ResponseError

from agent_from_scratch.errors import LLMError
from agent_from_scratch.llm import OpenAILLM
from agent_from_scratch.tools import create_default_tools


class _StubResponses:
    def __init__(self, response: Response):
        self.response = response

    def create(self, **_request: Any) -> Response:
        return self.response


def _llm_returning(response: Response) -> OpenAILLM:
    llm = object.__new__(OpenAILLM)
    llm.model = "gpt-test"
    llm.client = SimpleNamespace(responses=_StubResponses(response))
    return llm


def _response(
    *,
    output: list[Any],
    status: str = "completed",
    incomplete_details: IncompleteDetails | None = None,
    error: ResponseError | None = None,
) -> Response:
    return Response.model_construct(
        id="resp-test",
        created_at=0.0,
        error=error,
        incomplete_details=incomplete_details,
        instructions=None,
        metadata=None,
        model="gpt-test",
        object="response",
        output=output,
        parallel_tool_calls=True,
        temperature=None,
        tool_choice="auto",
        tools=[],
        top_p=None,
        status=status,
        text=None,
        truncation="disabled",
        usage=None,
    )


def _message(*content: ResponseOutputText | ResponseOutputRefusal) -> ResponseOutputMessage:
    return ResponseOutputMessage.model_construct(
        id="msg-test",
        content=list(content),
        role="assistant",
        status="completed",
        type="message",
    )


def _text(value: str) -> ResponseOutputText:
    return ResponseOutputText.model_construct(
        annotations=[],
        text=value,
        type="output_text",
        logprobs=[],
    )


def _refusal(value: str) -> ResponseOutputRefusal:
    return ResponseOutputRefusal.model_construct(refusal=value, type="refusal")


def _function_call(arguments: str) -> ResponseFunctionToolCall:
    return ResponseFunctionToolCall.model_construct(
        arguments=arguments,
        call_id="call-test",
        name="read_file",
        type="function_call",
        id="fc-test",
        status="completed",
    )


def test_openai_llm_normalizes_completed_text_response():
    raw = _response(output=[_message(_text("ready"))])

    normalized = _llm_returning(raw).generate([{"role": "user", "content": "go"}])

    assert normalized.content == "ready"
    assert normalized.finish_reason == "completed"
    assert normalized.status_detail is None
    assert normalized.tool_calls == []
    assert normalized.continuation_items == raw.output
    assert normalized.raw_response is raw


def test_openai_llm_preserves_incomplete_reason_and_partial_text():
    raw = _response(
        output=[_message(_text("partial answer"))],
        status="incomplete",
        incomplete_details=IncompleteDetails(reason="max_output_tokens"),
    )

    normalized = _llm_returning(raw).generate([])

    assert normalized.content == "partial answer"
    assert normalized.finish_reason == "incomplete"
    assert normalized.status_detail == "max_output_tokens"


def test_openai_llm_preserves_failed_error_code_and_message():
    raw = _response(
        output=[],
        status="failed",
        error=ResponseError(code="server_error", message="upstream failed"),
    )

    normalized = _llm_returning(raw).generate([])

    assert normalized.finish_reason == "failed"
    assert "server_error" in (normalized.status_detail or "")
    assert "upstream failed" in (normalized.status_detail or "")


def test_openai_llm_normalizes_completed_refusal_content():
    raw = _response(output=[_message(_refusal("I cannot help with that."))])

    normalized = _llm_returning(raw).generate([])

    assert normalized.content == "I cannot help with that."
    assert normalized.finish_reason == "refusal"
    assert normalized.status_detail == "I cannot help with that."


def test_openai_llm_prioritizes_function_calls_in_mixed_output():
    raw = _response(
        output=[
            _message(_text("I will inspect the file.")),
            _function_call('{"path":"README.md"}'),
        ]
    )

    normalized = _llm_returning(raw).generate([])

    assert normalized.content == "I will inspect the file."
    assert normalized.finish_reason == "tool_calls"
    assert len(normalized.tool_calls) == 1
    assert normalized.tool_calls[0].id == "call-test"
    assert normalized.tool_calls[0].name == "read_file"
    assert normalized.tool_calls[0].arguments == {"path": "README.md"}
    assert normalized.continuation_items == raw.output


def test_openai_llm_preserves_cancelled_status():
    normalized = _llm_returning(_response(output=[], status="cancelled")).generate([])

    assert normalized.finish_reason == "cancelled"
    assert normalized.status_detail is None


@pytest.mark.parametrize("status", ["queued", "in_progress"])
def test_openai_llm_rejects_non_terminal_synchronous_status(status: str):
    with pytest.raises(LLMError, match=status):
        _llm_returning(_response(output=[], status=status)).generate([])


@pytest.mark.parametrize(
    "arguments",
    ["[]", '"README.md"', "null", "42", "true"],
)
def test_openai_llm_rejects_function_arguments_that_are_not_objects(arguments: str):
    raw = _response(output=[_function_call(arguments)])

    with pytest.raises(LLMError, match="object"):
        _llm_returning(raw).generate([])


def _assert_strict_object_schemas(node: Any, *, path: str) -> None:
    if isinstance(node, list):
        for index, item in enumerate(node):
            _assert_strict_object_schemas(item, path=f"{path}[{index}]")
        return
    if not isinstance(node, dict):
        return

    node_type = node.get("type")
    if node_type == "object" or (
        isinstance(node_type, list) and "object" in node_type
    ):
        properties = node.get("properties")
        assert isinstance(properties, dict), f"{path} must define object properties"
        assert node.get("additionalProperties") is False, (
            f"{path} must reject additional properties"
        )
        assert set(node.get("required", [])) == set(properties), (
            f"{path} must require every property; optional values must be nullable"
        )

    for key, value in node.items():
        _assert_strict_object_schemas(value, path=f"{path}.{key}")


def test_default_tool_schemas_enable_strict_mode_recursively():
    schemas = [tool.as_schema() for tool in create_default_tools()]

    assert schemas
    for schema in schemas:
        assert schema.get("strict") is True, f"{schema['name']} must enable strict mode"
        _assert_strict_object_schemas(
            schema["parameters"],
            path=f"{schema['name']}.parameters",
        )
