"""Command line entrypoint for the tutorial harness skeleton."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import build_agent
from .eval import EvalCase, evaluate_run
from .failures import run_failure_corpus
from .replay import compare_records, load_run_record, make_run_record, save_run_record


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Learn Harness by Example skeleton.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run one scenario and save a run record.")
    run_parser.add_argument("--scenario", default="happy_path")
    run_parser.add_argument("--task", default="解释 agent harness 的作用，必须基于资料回答")
    run_parser.add_argument("--output", default="traces/harness/latest-run.json")
    run_parser.add_argument("--no-save", action="store_true")

    eval_parser = subparsers.add_parser("eval", help="Run the happy path eval.")
    eval_parser.add_argument("--scenario", default="happy_path")

    diagnose_parser = subparsers.add_parser("diagnose", help="Run the failure corpus.")
    diagnose_parser.add_argument("--cases", default="cases/failure_corpus.json")

    compare_parser = subparsers.add_parser("compare", help="Compare two saved run records.")
    compare_parser.add_argument("left")
    compare_parser.add_argument("right")

    args = parser.parse_args()

    if args.command == "run":
        agent = build_agent(scenario=args.scenario)
        state = agent.run(args.task)
        report = evaluate_run(
            state,
            EvalCase(
                name="requires evidence",
                task=args.task,
                required_terms=["基于"],
                trace_must_include=["tool.called", "tool.returned"],
            ),
        )
        record = make_run_record(
            state,
            config={"agent_version": args.scenario, "provider": "scenario-model", "eval_version": "rules-v2"},
            eval_report=report,
        )
        if not args.no_save:
            save_run_record(record, Path(args.output))
        print(json.dumps(record, ensure_ascii=False, indent=2))
        return

    if args.command == "eval":
        agent = build_agent(scenario=args.scenario)
        state = agent.run("解释 agent harness 的作用，必须基于资料回答")
        report = evaluate_run(
            state,
            EvalCase(
                name="requires evidence",
                task=state.task,
                required_terms=["基于", "运行", "观察", "评测", "复现"],
                trace_must_include=["tool.called", "tool.returned", "run.completed"],
                trace_must_not_include=["model.failed", "model.invalid_response"],
            ),
        )
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return

    if args.command == "diagnose":
        print(json.dumps(run_failure_corpus(Path(args.cases)), ensure_ascii=False, indent=2))
        return

    if args.command == "compare":
        print(json.dumps(compare_records(load_run_record(Path(args.left)), load_run_record(Path(args.right))), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

