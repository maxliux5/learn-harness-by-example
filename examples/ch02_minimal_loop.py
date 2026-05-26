"""Chapter 02: the first minimal Agent Loop."""

from __future__ import annotations


class MockModelClient:
    def complete(self, messages: list[dict]) -> dict:
        task = messages[-1]["content"]
        return {
            "content": f"我会围绕这个任务给出简短回答：{task}。Harness 的作用是让 Agent 可运行、可观察、可迭代。"
        }


class Agent:
    def __init__(self, model: MockModelClient) -> None:
        self.model = model

    def run(self, task: str) -> str:
        messages = [{"role": "user", "content": task}]
        response = self.model.complete(messages)
        return response["content"]


if __name__ == "__main__":
    agent = Agent(model=MockModelClient())
    print(agent.run("解释 agent harness 的作用"))

