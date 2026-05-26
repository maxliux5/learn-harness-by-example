"""Chapter 00: show why trace-aware eval matters."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from harness.core import build_agent
from harness.eval import EvalCase, evaluate_run
from harness.replay import compare_records, make_run_record, save_run_record


TASK = "解释 agent harness 的作用，必须基于资料回答"
TERMS = ["运行", "观察", "评测", "复现"]


def run_scenario(scenario: str, case: EvalCase) -> tuple[dict, dict]:
    agent = build_agent(scenario=scenario)
    state = agent.run(TASK)
    report = evaluate_run(state, case)
    record = make_run_record(
        state,
        config={"agent_version": scenario, "provider": "scenario-model", "eval_version": "case-study"},
        eval_report=report,
    )
    return report, record


if __name__ == "__main__":
    keyword_case = EvalCase(name="keyword-only", task=TASK, required_terms=TERMS)
    evidence_case = EvalCase(
        name="requires-tool-evidence",
        task=TASK,
        required_terms=TERMS,
        trace_must_include=["tool.called", "tool.returned"],
    )

    keyword_report, false_positive_record = run_scenario("eval_false_positive", keyword_case)
    evidence_report, _ = run_scenario("eval_false_positive", evidence_case)
    improved_report, improved_record = run_scenario("happy_path", evidence_case)

    output = {
        "task": TASK,
        "false_positive": {
            "answer": false_positive_record["answer"],
            "keyword_only_passed": keyword_report["passed"],
            "evidence_eval_passed": evidence_report["passed"],
            "missing_trace": evidence_report["missing_trace"],
            "trace_names": evidence_report["trace_names"],
        },
        "improved": {
            "answer": improved_record["answer"],
            "evidence_eval_passed": improved_report["passed"],
            "trace_names": improved_report["trace_names"],
        },
        "compare": compare_records(false_positive_record, improved_record),
        "lesson": "关键词能检查答案表面，Trace assertion 才能检查 Agent 是否真的走了证据路径。",
    }

    artifact_path = save_run_record(output, Path("traces/case-study-report.json"))
    output["artifact"] = str(artifact_path)
    print(json.dumps(output, ensure_ascii=False, indent=2))
