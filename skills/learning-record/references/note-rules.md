# Note Rules

Use this reference when converting course content or project work into durable notes.

## 1. Note Types

There are four preferred note types in this repository:

### Concept Note

Use for lessons such as Agent Loop, Tool Schema, Session, Memory, MCP, or Evaluation.

Include:

- definition
- key boundary
- why beginners misunderstand it
- how it affects project design

### Implementation Note

Use after building or refactoring something.

Include:

- target capability
- module boundary
- chosen design
- rejected alternative
- verification result

### Debug Note

Use after diagnosing a failure.

Include:

- symptom
- reproduction condition
- real cause
- fix
- prevention rule

### Review Note

Use after code review or architecture review.

Include:

- finding
- impact
- recommended change
- follow-up check

## 2. Compression Rules

Keep notes useful under future context pressure.

- Prefer bullet-resistant prose or short flat bullets.
- Remove filler like "this lesson was very important."
- Keep one note focused on one concept or one change.
- If the source is broad, extract only the rule that influences future implementation.

## 3. Mapping Course To Project

Always connect theory to one of these:

- `agent-from-scratch/` architecture
- current repository study structure
- tool design rules
- runtime/state design
- testing and evaluation habits
- debugging method

If the note cannot influence a future implementation choice, compress it further or skip it.

## 4. High-Value Prompts For Note Writing

When creating or updating a note, answer these questions:

- What is the one sentence rule?
- What mistake does this prevent?
- Where should this rule show up in code or architecture?
- How would I verify I actually understood it?
- What should I do differently next time?

## 5. Suggested File Usage

- Put long-lived cross-topic knowledge into `Agent学习笔记.md`
- Put interview-style distillations into `Agent面试题集.md`
- Put skill-local standards in this `skills/learning-record/` folder
- Create a new markdown file under the repo root or a dedicated notes folder only when the topic grows large enough to deserve its own artifact
