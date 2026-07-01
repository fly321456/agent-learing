---
name: agent-coding-rules
description: Enforce engineering rules for AI-generated code in this repository. Use when Codex needs to implement, refactor, debug, review, or extend agent-related code here and must stay aligned with the course's rules on architecture boundaries, message flow, tool design, testing, debugging, evaluation, and iterative engineering discipline.
---

# Agent Coding Rules

Use this skill for code work in this repository when correctness, structure, and long-term maintainability matter more than fast demo output.

## Repository Goal

This repository is not just for "making something run once." It is for turning Agent course understanding into reusable project ability and durable engineering artifacts.

That means every coding change should help at least one of these:

- clarify agent architecture
- improve runtime stability
- strengthen tool usability
- improve debugging visibility
- improve testing or evaluation
- preserve reusable learning

## Core Rules

1. Separate identity from execution.
Keep static agent definition, runtime control flow, tool dispatch, session state, memory behavior, and retry/error policy as distinct concerns whenever possible.

2. Treat context as a first-class runtime object.
Do not casually mix system instructions, user intent, tool outputs, summaries, and state updates into undifferentiated text.

3. Prefer small working slices.
Implement the narrowest complete step before adding more capability.

4. Design tools for model use, not only human use.
Tool names, descriptions, parameters, and outputs must reduce ambiguity for the model.

5. Make failure visible at the right boundary.
Do not hide errors with broad exception handling. Stop broken flow, surface the cause, and keep failures explainable.

6. Test stable boundaries early.
Start from helpers, tools, tool manager, session/message logic, and runner control flow before heavy end-to-end paths.

7. Improve by evidence, not feeling.
Use fixed cases, tests, traces, or explicit checks before concluding a prompt, tool, or architecture change is better.

## Coding Workflow

1. Read the relevant local files first.
Identify which layer is being changed: agent definition, runner, llm interface, tool manager, session, memory, or evaluation.

2. State the real boundary of the problem.
Many "model problems" are actually context-shaping, tool-interface, or runtime-order problems.

3. Make the smallest structurally correct change.
Avoid giant rewrites unless the current structure makes safe progress impossible.

4. Verify both behavior and boundary.
Check not just "does it work," but also "is it now in the right layer."

5. Leave artifacts that help future work.
Tests, traces, concise comments, or learning notes are preferred over hidden reasoning.

## Review Heuristics

Before considering the task done, ask:

- Did this change reduce or increase architectural mixing?
- Will the model have an easier time selecting and using tools correctly?
- Can a later engineer reconstruct what the runtime saw and did?
- Did we add verification close to the changed behavior?
- If it fails, will the next debugger know where to start?

## References

Read [references/repo-engineering-rules.md](./references/repo-engineering-rules.md) for:

- architecture boundary guidance for this repo
- prompt/message and session rules
- debugging order
- evaluation checklist
- tool redesign checklist
