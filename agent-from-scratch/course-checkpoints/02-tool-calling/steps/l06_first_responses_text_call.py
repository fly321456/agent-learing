from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys


CHECKPOINT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CHECKPOINT))

from responses_core import ScriptedResponse, ScriptedResponsesClient, generate_text  # noqa: E402


def offline_demo() -> None:
    client = ScriptedResponsesClient(
        [ScriptedResponse(output_text="An Observation is the recorded result of an action.")]
    )
    answer = generate_text(
        client,
        "course-model",
        "Answer with one precise sentence.",
        "What is an Observation?",
    )
    print("mode: offline")
    print(f"output_text: {answer}")


def online_demo() -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL")
    if not api_key or not model:
        raise SystemExit("Online mode requires OPENAI_API_KEY and OPENAI_MODEL")
    from openai import OpenAI

    response = OpenAI(api_key=api_key).responses.create(
        model=model,
        instructions="Answer with one precise sentence.",
        input="What is an Observation in an agent loop?",
    )
    print("mode: online")
    print(f"output_text: {response.output_text}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--online", action="store_true")
    args = parser.parse_args()
    online_demo() if args.online else offline_demo()

