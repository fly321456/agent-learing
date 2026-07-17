from __future__ import annotations

import agent_from_scratch.evaluation as evaluation
from agent_from_scratch.evaluation import EvalCase, load_cases


def test_every_safety_case_declares_an_outcome_oracle() -> None:
    safety_cases = [case for case in load_cases() if case.category == "safety"]

    assert safety_cases
    assert all(
        getattr(case, "expected_outcome", None) for case in safety_cases
    ), "Safety cases need outcome oracles; a matching tool name is not a safety result."


def test_expected_tool_playback_is_explicitly_named_protocol_replay() -> None:
    replay = getattr(evaluation, "run_protocol_replay", None)
    assert callable(replay), "Scripted expected-tool playback must be named protocol replay."

    summary = replay(load_cases())

    assert summary["total"] == 20
    assert summary["passed"] == 20
    assert summary["tool_calls"] == 25


def test_offline_eval_uses_executor_actual_instead_of_expected_tools() -> None:
    case = EvalCase(
        id="independent-actual",
        category="read",
        prompt="Read README.md",
        expected_tools=["read_file"],
        expected_outcome=None,
    )
    received_prompts: list[str] = []

    def executor(prompt: str):
        received_prompts.append(prompt)
        return {
            "actual_tools": [],
            "finish_reason": "completed",
            "steps": 1,
            "outcome": None,
        }

    summary = evaluation.run_offline_protocol_eval([case], executor=executor)

    assert received_prompts == [case.prompt]
    assert summary["total"] == 1
    assert summary["passed"] == 0
    assert summary["tool_calls"] == 0
    assert summary["failures"] == {"tool_sequence": 1}


def test_safety_eval_requires_actual_outcome_to_satisfy_oracle() -> None:
    cases = [
        EvalCase(
            id="blocked",
            category="safety",
            prompt="blocked attempt",
            expected_tools=["read_file"],
            expected_outcome="workspace_boundary_blocked",
        ),
        EvalCase(
            id="escaped",
            category="safety",
            prompt="escaped attempt",
            expected_tools=["read_file"],
            expected_outcome="workspace_boundary_blocked",
        ),
    ]
    actual_by_prompt = {
        "blocked attempt": "workspace_boundary_blocked",
        "escaped attempt": "workspace_read_succeeded",
    }

    def executor(prompt: str):
        return {
            "actual_tools": ["read_file"],
            "finish_reason": "completed",
            "steps": 1,
            "outcome": actual_by_prompt[prompt],
        }

    summary = evaluation.run_offline_protocol_eval(cases, executor=executor)

    assert summary["total"] == 2
    assert summary["passed"] == 1
    assert summary["failures"] == {"outcome_oracle": 1}
