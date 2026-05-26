"""Chapter 10: run the reusable harness skeleton end to end."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from harness.core import build_agent
from harness.eval import EvalCase, evaluate_run, summarize_results
from harness.replay import make_run_record, save_run_record


if __name__ == "__main__":
    agent = build_agent("happy_path")
    state = agent.run("解释 agent harness 的作用，必须基于资料回答")

    print("ANSWER")
    print(state.final_answer)

    print("\nTRACE")
    for event in state.trace:
        print(json.dumps(event.to_dict(), ensure_ascii=False))

    cases = [
        EvalCase(
            name="harness basics",
            task="解释 agent harness 的作用",
            required_terms=["运行", "观察", "评测", "复现"],
            trace_must_include=["tool.called", "tool.returned"],
        ),
        EvalCase(
            name="requires tool evidence",
            task="必须基于资料解释 agent harness",
            required_terms=["基于资料"],
            trace_must_include=["tool.called", "tool.returned", "run.completed"],
        ),
    ]
    eval_report = summarize_results([evaluate_run(agent.run(case.task), case) for case in cases])

    print("\nEVAL")
    print(json.dumps(eval_report, ensure_ascii=False, indent=2))

    record = make_run_record(
        state,
        config={"agent_version": "chapter-10", "provider": "scenario-model", "eval_version": "rules-v2"},
        eval_report=eval_report,
    )
    record_path = save_run_record(record, Path("traces/final/latest-run.json"))

    print("\nRECORD")
    print(record_path)
