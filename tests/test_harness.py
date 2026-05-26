from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from harness.core import build_agent
from harness.eval import EvalCase, evaluate_run
from harness.failures import run_failure_corpus
from harness.replay import compare_records, load_run_record, make_run_record, save_run_record


class HarnessSkeletonTest(unittest.TestCase):
    def test_happy_path_uses_tool_and_completes(self) -> None:
        state = build_agent("happy_path").run("解释 agent harness 的作用，必须基于资料回答")
        self.assertIn("tool.called", state.trace_names())
        self.assertIn("run.completed", state.trace_names())
        self.assertIn("基于资料", state.final_answer or "")
        self.assertEqual([], state.errors)

    def test_trace_assertion_catches_keyword_false_positive(self) -> None:
        state = build_agent("eval_false_positive").run("解释 agent harness 的作用，必须基于资料回答")
        result = evaluate_run(
            state,
            EvalCase(
                name="requires tool evidence",
                task=state.task,
                required_terms=["运行", "观察", "评测", "复现"],
                trace_must_include=["tool.called"],
            ),
        )
        self.assertFalse(result["passed"])
        self.assertEqual(["tool.called"], result["missing_trace"])

    def test_replay_roundtrip_and_compare(self) -> None:
        left = build_agent("no_tool_call").run("解释 agent harness 的作用，必须基于资料回答")
        right = build_agent("happy_path").run("解释 agent harness 的作用，必须基于资料回答")
        with tempfile.TemporaryDirectory() as tmp:
            left_path = save_run_record(make_run_record(left, {"agent_version": "left"}), Path(tmp) / "left.json")
            right_path = save_run_record(make_run_record(right, {"agent_version": "right"}), Path(tmp) / "right.json")
            comparison = compare_records(load_run_record(left_path), load_run_record(right_path))
        self.assertEqual(1, comparison["tool_call_delta"])
        self.assertTrue(comparison["answer_changed"])

    def test_failure_corpus_runs(self) -> None:
        report = run_failure_corpus()
        self.assertEqual(9, report["total"])
        self.assertEqual(9, report["detected"])


if __name__ == "__main__":
    unittest.main()
