"""Chapter 04: add tools to the Agent Loop."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


KnowledgeBase = {
    "harness": "Agent Harness 负责运行、约束、观察、评测和复现 Agent 行为。",
    "trace": "Trace 是一次运行的结构化事件时间线。",
}


@dataclass
class Tool:
    name: str
    description: str
    handler: Callable[[dict], dict]


class MockToolCallingModel:
    def complete(self, messages: list[dict]) -> dict:
        if not any(message["role"] == "tool" for message in messages):
            return {"type": "tool_call", "tool": "search", "args": {"query": "harness"}}

        tool_result = messages[-1]["content"]
        return {
            "type": "final",
            "content": f"基于工具结果：{tool_result} 因此，harness 让 Agent 更容易工程化。",
        }


class Agent:
    def __init__(self, model: MockToolCallingModel, tools: list[Tool]) -> None:
        self.model = model
        self.tools = {tool.name: tool for tool in tools}

    def run(self, task: str) -> str:
        messages = [{"role": "user", "content": task}]

        for _ in range(4):
            response = self.model.complete(messages)
            if response["type"] == "final":
                return response["content"]

            tool = self.tools.get(response["tool"])
            if tool is None:
                messages.append({"role": "tool", "name": response["tool"], "content": f"工具不存在：{response['tool']}"})
                continue

            try:
                result = tool.handler(response.get("args", {}))
            except Exception as exc:
                result = {"content": f"工具调用失败：{exc}"}
            messages.append({"role": "tool", "name": tool.name, "content": result["content"]})

        return "运行超过最大步数，未得到最终答案。"


def search(args: dict) -> dict:
    if "query" not in args:
        return {"content": "工具参数错误：缺少 query。"}
    query = args.get("query", "").lower()
    return {"content": KnowledgeBase.get(query, "没有找到相关资料。")}


if __name__ == "__main__":
    agent = Agent(
        model=MockToolCallingModel(),
        tools=[Tool(name="search", description="Search local knowledge base", handler=search)],
    )
    print(agent.run("研究 agent harness 的作用"))
