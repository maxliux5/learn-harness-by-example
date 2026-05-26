"""Failure corpus loader and diagnosis runner."""

from __future__ import annotations

import json
from pathlib import Path

from .core import build_agent
from .eval import EvalCase, evaluate_run, summarize_results


DEFAULT_CASE_PATH = Path("cases/failure_corpus.json")


def load_failure_corpus(path: Path = DEFAULT_CASE_PATH) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def case_to_eval(case: dict) -> EvalCase:
    rule = case.get("eval", {})
    return EvalCase(
        name=case["id"],
        task=case["task"],
        required_terms=rule.get("required_terms", []),
        forbidden_terms=rule.get("forbidden_terms", []),
        trace_must_include=rule.get("trace_must_include", []),
        trace_must_not_include=rule.get("trace_must_not_include", []),
        expected_error_terms=rule.get("expected_error_terms", []),
    )


def run_failure_corpus(path: Path = DEFAULT_CASE_PATH) -> dict:
    results = []
    for case in load_failure_corpus(path):
        agent = build_agent(scenario=case["scenario"], max_steps=case.get("max_steps", 4))
        state = agent.run(case["task"])
        result = evaluate_run(state, case_to_eval(case))
        result["detected"] = result["passed"]
        result["scenario"] = case["scenario"]
        result["expected_diagnosis"] = case["expected_diagnosis"]
        results.append(result)
    return {
        "detected": sum(1 for result in results if result["detected"]),
        "total": len(results),
        "results": results,
    }
