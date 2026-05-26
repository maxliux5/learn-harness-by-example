"""Chapter 03: make the model provider replaceable."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class ModelClient(Protocol):
    def complete(self, messages: list[dict]) -> dict:
        """Return a response with at least a content field."""


@dataclass
class MockModelClient:
    label: str = "mock"

    def complete(self, messages: list[dict]) -> dict:
        return {
            "content": "Mock provider: harness 是 Agent 的运行、观察和评测外壳。",
            "raw": {"provider": self.label},
        }


class EchoModelClient:
    def complete(self, messages: list[dict]) -> dict:
        return {
            "content": f"Echo provider saw {len(messages)} message(s): {messages[-1]['content']}",
            "raw": {"provider": "echo", "messages": messages},
        }


class Agent:
    def __init__(self, model: ModelClient) -> None:
        self.model = model

    def run(self, task: str) -> str:
        messages = [{"role": "user", "content": task}]
        return self.model.complete(messages)["content"]


if __name__ == "__main__":
    for model in [MockModelClient(), EchoModelClient()]:
        agent = Agent(model=model)
        print(agent.run("什么是 harness?"))

