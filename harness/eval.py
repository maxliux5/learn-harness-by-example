"""Eval rules that inspect both final answers and trace behavior."""

from __future__ import annotations

from dataclasses import dataclass, field

from .state import RunState


@dataclass
class EvalCase:
    name: str
    task: str
    required_terms: list[str] = field(default_factory=list)
    forbidden_terms: list[str] = field(default_factory=list)
    trace_must_include: list[str] = field(default_factory=list)
    trace_must_not_include: list[str] = field(default_factory=list)
    expected_error_terms: list[str] = field(default_factory=list)


def evaluate_run(state: RunState, case: EvalCase) -> dict:
    answer = state.final_answer or ""
    trace_names = state.trace_names()
    missing_terms = [term for term in case.required_terms if term not in answer]
    forbidden_terms = [term for term in case.forbidden_terms if term in answer]
    missing_trace = [name for name in case.trace_must_include if name not in trace_names]
    forbidden_trace = [name for name in case.trace_must_not_include if name in trace_names]
    error_text = "\n".join(state.errors)
    missing_error_terms = [term for term in case.expected_error_terms if term not in error_text]

    passed = not any([missing_terms, forbidden_terms, missing_trace, forbidden_trace, missing_error_terms])
    return {
        "name": case.name,
        "passed": passed,
        "missing_terms": missing_terms,
        "forbidden_terms": forbidden_terms,
        "missing_trace": missing_trace,
        "forbidden_trace": forbidden_trace,
        "missing_error_terms": missing_error_terms,
        "answer": answer,
        "errors": state.errors,
        "trace_names": trace_names,
    }


def summarize_results(results: list[dict]) -> dict:
    return {
        "passed": sum(1 for result in results if result["passed"]),
        "total": len(results),
        "results": results,
    }

