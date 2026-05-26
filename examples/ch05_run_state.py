"""Chapter 05: return structured RunState from an agent run."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field


@dataclass
class RunState:
    task: str
    messages: list[dict] = field(default_factory=list)
    tool_calls: list[dict] = field(default_factory=list)
    final_answer: str | None = None
    errors: list[str] = field(default_factory=list)


class MockModel:
    def complete(self, messages: list[dict]) -> dict:
        if not any(message["role"] == "tool" for message in messages):
            return {"type": "tool_call", "tool": "search", "args": {"query": "trace"}}
        return {"type": "final", "content": "Trace 让 harness 能检查每一步发生了什么。"}


def search(args: dict) -> dict:
    data = {"trace": "Trace 是模型调用和工具调用的结构化事件流。"}
    return {"content": data.get(args.get("query"), "没有找到结果。")}


class Agent:
    def __init__(self, model: MockModel) -> None:
        self.model = model

    def run(self, task: str) -> RunState:
        state = RunState(task=task)
        state.messages.append({"role": "user", "content": task})

        for _ in range(4):
            response = self.model.complete(state.messages)
            if response["type"] == "final":
                state.final_answer = response["content"]
                state.messages.append({"role": "assistant", "content": response["content"]})
                return state

            if response["tool"] != "search":
                state.errors.append(f"Unknown tool: {response['tool']}")
                continue

            result = search(response["args"])
            state.tool_calls.append({"tool": "search", "args": response["args"], "result": result})
            state.messages.append({"role": "tool", "name": "search", "content": result["content"]})

        state.errors.append("Max steps exceeded")
        return state


if __name__ == "__main__":
    run = Agent(MockModel()).run("解释 trace 的作用")
    print(json.dumps(asdict(run), ensure_ascii=False, indent=2))

