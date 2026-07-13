import pytest

from agent_from_scratch.cli import build_parser
from agent_from_scratch.config import RuntimeConfig
from agent_from_scratch.errors import LLMError
from agent_from_scratch.llm import OpenAILLM


def test_runtime_config_reads_environment_without_hardcoding_latest_model(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENAI_MODEL", "test-model")
    monkeypatch.setenv("AGENT_MAX_STEPS", "3")
    monkeypatch.setenv("AGENT_WORKSPACE", str(tmp_path))

    config = RuntimeConfig.from_env()

    assert config.model == "test-model"
    assert config.max_steps == 3
    assert config.workspace == tmp_path.resolve()


def test_runtime_config_has_no_permanent_model_default(monkeypatch):
    monkeypatch.delenv("OPENAI_MODEL", raising=False)

    config = RuntimeConfig.from_env()

    assert config.model is None


def test_openai_adapter_requires_an_explicit_model(monkeypatch):
    monkeypatch.delenv("OPENAI_MODEL", raising=False)

    with pytest.raises(LLMError, match="model"):
        OpenAILLM(api_key="test-key")


def test_cli_exposes_run_resume_session_and_trace_options():
    parser = build_parser()

    args = parser.parse_args(
        [
            "review this repository",
            "--workspace",
            ".",
            "--max-steps",
            "4",
            "--session",
            "demo",
            "--trace",
            "trace.jsonl",
        ]
    )

    assert args.prompt == "review this repository"
    assert args.max_steps == 4
    assert args.session == "demo"
    assert args.trace.name == "trace.jsonl"


def test_cli_resume_mode_only_requires_a_run_id():
    args = build_parser().parse_args(["--resume", "run-123"])

    assert args.prompt is None
    assert args.resume == "run-123"
