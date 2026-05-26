---
name: agent-harness-reviewer
description: Review whether an agent project has enough harness depth to debug, eval, and replay runs.
version: 1.0.0
tags: [agent, harness, review, eval, trace]
---

# Agent Harness Reviewer

Use this skill to review an agent project for operational depth.

## Checklist

1. Identify the single public run entrypoint.
2. Check whether model providers are behind a replaceable boundary.
3. Check whether tools have structured names, args, returns, and errors.
4. Check whether one run has a durable state object.
5. Check whether trace events cover model calls, tool calls, errors, and termination.
6. Check whether evals inspect both final answer and trace behavior.
7. Check whether failures become reusable cases.
8. Check whether run records can be saved and compared across versions.

## Output

Return:

- `strengths`: what is already inspectable
- `gaps`: what will be hard to debug later
- `highest_leverage_fix`: one change that improves the harness most
- `missing_trace_events`: event names the project should add
- `eval_assertions`: checks that would catch the most likely false positives
