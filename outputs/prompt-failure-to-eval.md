---
name: failure-to-eval-case
description: Convert a bad agent run into a small EvalCase and failure-corpus entry.
tags: [agent, eval, failure-corpus]
---

You are writing eval cases for a minimal agent harness.

Given a failure report, produce:

1. A one-sentence failure title.
2. A minimal task that reproduces the failure.
3. The expected diagnosis from trace evidence.
4. Required answer terms, if the answer text matters.
5. Forbidden answer terms, if hallucination or unsupported claims matter.
6. Required trace events.
7. Forbidden trace events.
8. Expected error text, if the failure should surface in `state.errors`.

Return JSON shaped like:

```json
{
  "id": "short_snake_case_id",
  "title": "Human-readable title",
  "scenario": "scenario_name",
  "task": "task text",
  "expected_diagnosis": "what trace evidence should show",
  "eval": {
    "required_terms": [],
    "forbidden_terms": [],
    "trace_must_include": [],
    "trace_must_not_include": [],
    "expected_error_terms": []
  }
}
```

Keep the case narrow. One failure should teach one debugging lesson.
