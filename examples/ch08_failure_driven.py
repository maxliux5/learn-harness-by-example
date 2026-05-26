"""Chapter 08: turn a failure into a repeatable improvement check."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Run:
    version: str
    answer: str
    trace: list[dict] = field(default_factory=list)


@dataclass
class EvalCase:
    name: str
    task: str
    requires_tool: bool
    required_answer_terms: list[str]


def trace_event(name: str, payload: dict | None = None) -> dict:
    return {
        "name": name,
        "payload": payload or {},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def baseline_agent(task: str) -> Run:
    return Run(
        version="baseline",
        answer="Harness 很重要，因为它让 Agent 更可靠。",
        trace=[
            trace_event("run.started", {"task": task}),
            trace_event("model.final", {"note": "answered without evidence"}),
        ],
    )


def improved_agent(task: str) -> Run:
    tool_result = "本地资料：Harness 负责运行、观察、评测和复现 Agent 行为。"
    return Run(
        version="improved",
        answer=f"基于搜索结果：{tool_result}",
        trace=[
            trace_event("run.started", {"task": task}),
            trace_event("tool.called", {"tool": "search", "query": "harness"}),
            trace_event("tool.returned", {"content": tool_result}),
            trace_event("model.final", {"note": "answered with evidence"}),
        ],
    )


def evaluate_run(case: EvalCase, run: Run) -> dict:
    used_tool = any(event["name"] == "tool.called" for event in run.trace)
    missing_terms = [term for term in case.required_answer_terms if term not in run.answer]
    tool_requirement_met = used_tool if case.requires_tool else True
    return {
        "case": case.name,
        "version": run.version,
        "passed": tool_requirement_met and not missing_terms,
        "used_tool": used_tool,
        "missing_terms": missing_terms,
    }


if __name__ == "__main__":
    case = EvalCase(
        name="must answer with tool evidence",
        task="解释 harness 的作用，必须基于资料回答",
        requires_tool=True,
        required_answer_terms=["基于", "资料"],
    )
    runs = [baseline_agent(case.task), improved_agent(case.task)]
    report = {"checks": [evaluate_run(case, run) for run in runs], "runs": [run.__dict__ for run in runs]}
    print(json.dumps(report, ensure_ascii=False, indent=2))
