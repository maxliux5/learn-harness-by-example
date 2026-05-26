from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from harness.core import build_agent
from harness.eval import EvalCase, evaluate_run
from harness.failures import run_failure_corpus
from harness.providers import MiniMaxModelClient
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

    def test_minimax_provider_uses_env_key_and_tool_first_policy(self) -> None:
        with patch.dict("os.environ", {"MINIMAX_API_KEY": "test-key"}, clear=True):
            model = MiniMaxModelClient.from_env(transport=lambda _: {})

        response = model.complete([{"role": "user", "content": "解释 agent harness"}])

        self.assertEqual({"type": "tool_call", "tool": "search", "args": {"query": "agent harness"}}, response)

    def test_minimax_provider_converts_chat_completion_to_final_response(self) -> None:
        requests: list[dict] = []

        def fake_transport(request: dict) -> dict:
            requests.append(request)
            return {
                "choices": [
                    {
                        "message": {
                            "content": "基于资料：Agent Harness 让运行、观察、评测和复现都有证据。"
                        }
                    }
                ],
                "usage": {"total_tokens": 42},
            }

        model = MiniMaxModelClient(api_key="test-key", model="MiniMax-M2.7", transport=fake_transport)
        response = model.complete(
            [
                {"role": "user", "content": "解释 agent harness 的作用，必须基于资料回答"},
                {"role": "tool", "name": "search", "content": "Agent Harness 负责运行、观察、评测和复现。"},
            ]
        )

        self.assertEqual("final", response["type"])
        self.assertIn("基于资料", response["content"])
        self.assertEqual("MiniMax-M2.7", requests[0]["model"])
        self.assertEqual("test-key", requests[0]["api_key"])
        self.assertIn("Agent Harness 负责运行", requests[0]["messages"][1]["content"])

    def test_minimax_provider_normalizes_host_and_strips_thinking_blocks(self) -> None:
        requests: list[dict] = []

        def fake_transport(request: dict) -> dict:
            requests.append(request)
            return {
                "choices": [
                    {
                        "message": {
                            "content": "<think>internal reasoning</think>\n\n基于资料：Agent Harness 可运行、可观察、可评测、可复现。"
                        }
                    }
                ]
            }

        model = MiniMaxModelClient(api_key="test-key", base_url="https://api.minimaxi.com", transport=fake_transport)
        response = model.complete(
            [
                {"role": "user", "content": "解释 agent harness"},
                {"role": "tool", "name": "search", "content": "Agent Harness 负责运行、观察、评测和复现。"},
            ]
        )

        self.assertEqual("https://api.minimaxi.com/v1", requests[0]["base_url"])
        self.assertEqual("基于资料：Agent Harness 可运行、可观察、可评测、可复现。", response["content"])

    def test_minimax_provider_retries_transient_transport_errors(self) -> None:
        attempts = 0

        def flaky_transport(_: dict) -> dict:
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise TimeoutError("temporary timeout")
            return {"choices": [{"message": {"content": "基于资料：Agent Harness 可运行、可观察、可评测、可复现。"}}]}

        model = MiniMaxModelClient(api_key="test-key", transport=flaky_transport, retries=1)
        response = model.complete(
            [
                {"role": "user", "content": "解释 agent harness"},
                {"role": "tool", "name": "search", "content": "Agent Harness 负责运行、观察、评测和复现。"},
            ]
        )

        self.assertEqual(2, attempts)
        self.assertEqual("final", response["type"])


if __name__ == "__main__":
    unittest.main()
