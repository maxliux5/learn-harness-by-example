"""Chapter 06: emit trace events as JSONL."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone


@dataclass
class TraceEvent:
    name: str
    payload: dict
    timestamp: str


class TraceRecorder:
    def __init__(self) -> None:
        self.events: list[TraceEvent] = []

    def record(self, name: str, payload: dict) -> None:
        self.events.append(
            TraceEvent(
                name=name,
                payload=payload,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        )

    def to_jsonl(self) -> str:
        return "\n".join(json.dumps(asdict(event), ensure_ascii=False) for event in self.events)


class MockModel:
    def complete(self, messages: list[dict]) -> dict:
        if not any(message["role"] == "tool" for message in messages):
            return {"type": "tool_call", "tool": "search", "args": {"query": "eval"}}
        return {"type": "final", "content": "Eval 把 demo 变成可重复检查的基准。"}


def search(args: dict) -> dict:
    data = {"eval": "Eval 是一组固定任务和透明评分规则。"}
    return {"content": data.get(args.get("query"), "没有找到结果。")}


class Agent:
    def __init__(self, model: MockModel, trace: TraceRecorder) -> None:
        self.model = model
        self.trace = trace

    def run(self, task: str) -> str:
        messages = [{"role": "user", "content": task}]
        self.trace.record("run.started", {"task": task})

        for step in range(4):
            self.trace.record("model.called", {"step": step, "message_count": len(messages)})
            response = self.model.complete(messages)
            self.trace.record("model.returned", {"step": step, "response_type": response["type"]})

            if response["type"] == "final":
                self.trace.record("run.completed", {"answer": response["content"]})
                return response["content"]

            self.trace.record("tool.called", {"tool": response["tool"], "args": response["args"]})
            result = search(response["args"])
            self.trace.record("tool.returned", {"tool": response["tool"], "result": result})
            messages.append({"role": "tool", "name": response["tool"], "content": result["content"]})

        self.trace.record("run.failed", {"reason": "max_steps_exceeded"})
        return "未得到最终答案。"


if __name__ == "__main__":
    trace = TraceRecorder()
    answer = Agent(MockModel(), trace).run("说明 eval 的作用")
    print(answer)
    print("\nTRACE JSONL")
    print(trace.to_jsonl())

