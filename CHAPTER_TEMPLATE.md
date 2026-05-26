# Chapter Template

Use this template when adding or rewriting a chapter. The goal is to keep the course readable, runnable, and inspectable.

## File Contract

Each chapter should usually touch these files:

```text
docs/chapters/NN-topic.md
examples/chNN_topic.py
traces/<optional-artifact>.json
outputs/<optional-reusable-artifact>.md
```

## Documentation Format

````markdown
# NN Chapter Title

[Two or three short paragraphs. Start from a concrete agent engineering pain, not a definition.]

## Learning Goals

- [What the reader should understand]
- [What the reader should be able to run]
- [What signal they should inspect]

## The Problem

[A specific failure, design pressure, or debugging question.]

## Minimal Code

[Introduce the smallest implementation that exposes the concept.]

## Run It

```bash
python3 examples/chNN_topic.py
```

[Explain the important output fields.]

## Observe The Trace Or Eval

[Name the trace events, eval fields, or replay diff that prove the behavior.]

## What This Prevents

[Show the mistake this layer catches.]

## Exercises

1. [Small change]
2. [Failure injection]
3. [Extension toward the final harness]

## Checkpoint

[3-5 questions the reader should now be able to answer.]
````

## Code Guidelines

- Use the Python standard library unless the chapter is explicitly about a dependency.
- Keep the file runnable from the repo root.
- Prefer deterministic doubles over live LLM calls.
- Print JSON when the reader should inspect structure.
- If a chapter introduces a behavior, add a trace or eval signal that proves it.

## Artifact Guidelines

Every chapter should ship at least one artifact:

- runnable script
- trace sample
- eval report
- replay record
- failure corpus case
- reusable prompt
- reusable skill
- package module

The artifact is the proof that the chapter taught something operational, not only conceptual.
