"""Deterministic model doubles that simulate real agent failure modes."""

from __future__ import annotations

from typing import Protocol


class ModelClient(Protocol):
    def complete(self, messages: list[dict]) -> dict:
        """Return either a final answer or a tool call."""


class ScenarioModel:
    """A deterministic model double for teaching harness behavior.

    Each scenario represents a failure mode that a real provider/model/tool
    workflow can produce. This keeps the tutorial offline while still forcing
    the harness through messy paths.
    """

    def __init__(self, scenario: str = "happy_path") -> None:
        self.scenario = scenario
        self.calls = 0

    def complete(self, messages: list[dict]) -> dict:
        self.calls += 1
        has_tool_result = any(message.get("role") == "tool" for message in messages)

        if self.scenario == "provider_timeout":
            raise TimeoutError("mock provider timed out")

        if self.scenario == "schema_drift":
            return {"kind": "tool", "name": "search", "arguments": {"query": "agent harness"}}

        if self.scenario == "no_tool_call":
            return {"type": "final", "content": "Harness 很重要，因为它让 Agent 更可靠。"}

        if self.scenario == "hallucinated_citation":
            return {
                "type": "final",
                "content": "根据 Smith 2027 的研究，Harness 可以自动保证 Agent 正确。",
            }

        if self.scenario == "eval_false_positive":
            return {
                "type": "final",
                "content": "Agent Harness 包含运行、观察、评测和复现，但这句话没有任何资料证据。",
            }

        if self.scenario == "wrong_tool_args" and not has_tool_result:
            return {"type": "tool_call", "tool": "search", "args": {"query": "unknown topic"}}

        if self.scenario == "missing_tool_args" and not has_tool_result:
            return {"type": "tool_call", "tool": "search", "args": {}}

        if self.scenario == "empty_tool_result" and not has_tool_result:
            return {"type": "tool_call", "tool": "search", "args": {"query": "empty"}}

        if self.scenario == "max_step_loop":
            return {"type": "tool_call", "tool": "search", "args": {"query": "agent harness"}}

        if not has_tool_result:
            return {"type": "tool_call", "tool": "search", "args": {"query": "agent harness"}}

        evidence = messages[-1].get("content", "")
        return {
            "type": "final",
            "content": f"基于资料：{evidence} 总结：Agent Harness 让 Agent 可运行、可观察、可评测、可复现。",
        }

