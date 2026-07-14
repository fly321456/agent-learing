# 01 Agent Concepts

Module 1 teaches the Agent mental model with deterministic, offline Python.

## Run the final checkpoint

```powershell
python demo.py
```

Expected final line:

```text
finish_reason: completed
```

## Run each lesson step

```powershell
python steps/l01_single_shot_vs_agent.py
python steps/l02_four_elements.py
python steps/l03_workflow_vs_agent.py
python steps/l04_think_act_observe.py
```

## Verify behavior

From `agent-from-scratch/`:

```powershell
python -m pytest -q tests/test_course_module1.py
```

The teaching API is intentionally small: `ScriptedLLM.decide(task, observations)`, a `TOOLS` registry, and `run_agent(..., max_steps)`. It is not the public Runtime API.
