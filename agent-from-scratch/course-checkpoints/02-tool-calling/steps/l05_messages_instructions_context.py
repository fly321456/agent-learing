from __future__ import annotations


def build_request(task: str) -> dict:
    return {
        "model": "course-model",
        "instructions": "You are a careful coding assistant. Use only supplied facts.",
        "input": [
            {"role": "developer", "content": "Answer in one sentence."},
            {"role": "user", "content": task},
        ],
    }


if __name__ == "__main__":
    request = build_request("Explain why a missing README is an observation.")
    print(f"instructions: {request['instructions']}")
    for message in request["input"]:
        print(f"message[{message['role']}]: {message['content']}")
    print("context: instructions + input carried by this request")

