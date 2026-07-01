---
name: learning-record
description: Capture course learning, project practice, debugging takeaways, architectural understanding, and iteration notes into structured records. Use when Codex needs to turn scattered study content, implementation experience, code reading results, or review conclusions into reusable learning notes for this repository.
---

# Learning Record

Use this skill to keep study and project progress cumulative instead of fragmented. The goal is not to write pretty notes. The goal is to preserve decisions, understanding, mistakes, and reusable patterns so later work starts from a higher baseline.

## What To Record

Record only information that will help future work in this repository:

- core concept understanding from course materials
- what was implemented in the project and why
- what failed, why it failed, and how it was fixed
- architecture boundaries and design tradeoffs
- repeated debugging patterns
- evaluation or verification results

Do not turn notes into long transcript-style summaries of everything that happened.

## Record Structure

When adding a new note, prefer this shape:

1. Topic
2. Why it matters
3. Core understanding
4. Project mapping
5. Common mistakes or failure signals
6. Verification or evidence
7. Next action

## Writing Rules

- Write for future implementation, not for passive review.
- Prefer concrete statements over motivational language.
- Preserve key terms from the codebase and course.
- Separate "what the concept means" from "how this repo should use it."
- If a lesson changes how code should be written, state the rule explicitly.
- If the note comes from debugging, include the observable symptom and the real cause.
- If the note comes from refactoring, include what boundary became clearer.

## Repository Convention

Use these files:

- `skills/learning-record/assets/learning-log-template.md` for new entries
- `skills/learning-record/references/note-rules.md` for detailed guidance
- root notes such as `Agent学习笔记.md` when updating the central knowledge base

## Good Outcomes

A good learning record should let a later agent or engineer answer:

- What did we learn?
- Why does it matter for this repository?
- What coding or design rule changed because of it?
- What evidence do we have?
- What should be done next?
