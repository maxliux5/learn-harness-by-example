"""Run the tutorial harness against the real MiniMax chat completions API.

Set MINIMAX_API_KEY in your environment before running:

    python3 examples/minimax_smoke.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from harness.core import build_agent
from harness.eval import EvalCase, evaluate_run
from harness.replay import make_run_record, save_run_record


TASK = "解释 agent harness 的作用，必须基于资料回答"


if __name__ == "__main__":
    state = build_agent(provider="minimax").run(TASK)
    report = evaluate_run(
        state,
        EvalCase(
            name="minimax requires local evidence",
            task=TASK,
            required_terms=["基于", "运行", "观察", "评测", "复现"],
            trace_must_include=["tool.called", "tool.returned", "run.completed"],
            trace_must_not_include=["model.failed", "model.invalid_response"],
        ),
    )
    record = make_run_record(
        state,
        config={"agent_version": "MiniMax-M2.7", "provider": "minimax", "eval_version": "rules-v2"},
        eval_report=report,
    )
    path = save_run_record(record, Path("traces/minimax/latest-run.json"))
    print(json.dumps({"path": str(path), "record": record}, ensure_ascii=False, indent=2))
