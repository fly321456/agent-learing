# ADR 001: Runtime safety and evaluation contracts

- Status: Accepted for the course candidate release
- Date: 2026-07-17

## Context

The course runtime is executable reference code. Ambiguous tool schemas, path traversal, unbounded observations, unsafe approval display, repeated side effects after resume, and self-fulfilling evaluation fixtures would teach unsafe patterns even when demos pass.

## Decision

The final runtime uses strict function schemas, validates arguments again at execution time, contains file access to the resolved workspace, bounds observations, redacts traces and approval previews, and fails closed when risk classification or approval is missing. Exact patches reject empty matches, preserve newline bytes, and replace files atomically.

Provider statuses and refusal blocks are normalized into explicit `LLMResponse` outcomes. Sessions use typed messages and turn identifiers. Checkpoints persist completed call IDs and reuse matching results during resume. This reduces duplicate side effects but is not a transactional exactly-once guarantee: a process can still fail between an external side effect and durable checkpoint replacement.

Protocol replay is named and reported as transport-plumbing evidence only. Agent-quality evaluation must receive independently produced actual behavior and compare it with frozen tool and outcome oracles. Multi-agent comparisons use independent validity labels and count both false acceptance and false rejection.

## Alternatives considered

- Trust model-generated arguments because the API used strict mode. Rejected because local validation is the final execution boundary.
- Default unspecified tools to read-only. Rejected because an omitted classification could silently bypass approval.
- Treat scripted expected calls as measured agent quality. Rejected because expected behavior would generate its own actual result.
- Claim exactly-once execution from a JSON checkpoint. Rejected because durable distributed side effects require idempotency keys or transactional infrastructure.

## Consequences

Some extension code must classify tools explicitly or handle approval. Observations may be truncated. Resume is safer but callers still need idempotent external operations. Evaluation reports are more conservative and must disclose whether they measure plumbing, deterministic behavior, or an online model.
