# Repo Engineering Rules

This reference adapts the course principles to the current repository.

## 1. Repository Positioning

The repository has three active roles:

- `课程/` builds conceptual understanding
- `agent-from-scratch/` turns concepts into code
- root notes and local skills preserve reusable knowledge

Therefore, coding work should not drift into isolated demo hacking. It should strengthen the mapping between lesson, implementation, and reusable rule.

## 2. Architecture Boundaries

Prefer these conceptual separations:

- `Agent`: static definition, identity, instructions, tools, model choice
- `Runner`: loop execution, turn progression, stop conditions, orchestration
- `LLM interface`: provider abstraction and request/response handling
- `ToolManager`: registration, schema exposure, execution dispatch
- `Session`: ordered runtime context and message history
- `Memory`: retrieval/write behavior distinct from session flow
- `Evaluation`: fixed cases and measurable outcomes

If the current code violates these boundaries, move toward them gradually rather than rewriting everything at once.

## 3. Prompt And Message Discipline

The course treats messages as runtime state, not random strings.

Preferred rules:

- system instructions come from agent configuration
- user intent enters as explicit user input
- tool results are appended as structured context, not disguised user text
- session owns message order and continuity

Smells:

- duplicated prompt fragments across modules
- tool output inserted as fake user requests
- impossible-to-reconstruct final model context
- repeated tool calls caused by unclear prior results

## 4. Tool Design Rules

Each tool should be reviewed as an interface product for the model.

Check:

- Is the name explicit?
- Does the description explain when to use it?
- Are parameters minimal and unambiguous?
- Is the output concise, structured, and useful for the next step?
- Is the tool narrower than a vague "manager" abstraction?

Typical refactors:

- rename overloaded tools
- simplify parameter schema
- split one mega-tool into several focused tools
- improve returned structure for downstream reasoning

## 5. Testing Order

For this repository, prefer verifying in this order:

1. utility or pure logic behavior
2. tool behavior
3. tool manager registration and execution
4. session/message shaping
5. runner behavior with fake model responses
6. selected integrated runs

The purpose is to keep the verification surface stable while the harness is still evolving.

## 6. Error Handling Rules

Use boundary-aware failure handling:

- tool layer: unknown tool, bad args, execution failure
- llm layer: provider/auth/request failure
- runner layer: stop or surface the failure instead of looping blindly

Bad pattern:

```python
try:
    ...
except:
    pass
```

Preferred outcome:

- failure is visible
- failure source is understandable
- runtime state does not silently continue in corruption

## 7. Debugging Order

When the result is wrong, inspect in this order:

1. intended task and input
2. final context sent to the model
3. tool selection, arguments, and outputs
4. memory/session injection
5. runtime order, retry, timeout, loop behavior
6. only then prompt/model decision quality

This avoids the common mistake of immediately blaming the model.

## 8. Minimal Evaluation Checklist

For meaningful changes, record at least some of:

- task success
- correct tool selection
- unnecessary tool calls
- average turn count
- runtime cost or latency
- obvious failure cases

Even a markdown checklist or table is enough if it uses fixed cases.

## 9. Learning Loop

Whenever a coding change teaches a reusable lesson, update learning artifacts too:

- `Agent学习笔记.md` for long-lived knowledge
- `skills/learning-record/` when formalizing note-taking rules
- new topic notes only when the content deserves a separate durable file
