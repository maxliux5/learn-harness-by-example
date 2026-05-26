"""Chapter 01: compare a naive agent with a harnessed run."""

from __future__ import annotations

import json
from datetime import datetime, timezone


def naive_research(question: str) -> str:
    return f"结论：{question} 需要 harness，因为 harness 让 Agent 更容易迭代。"


def harnessed_research(question: str) -> dict:
    trace = [
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "name": "run.started",
            "payload": {"question": question},
        },
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "name": "model.completed",
            "payload": {"provider": "mock", "message_count": 1},
        },
    ]
    answer = "结论：Agent Harness 把一次运行变成可观察、可复现、可评测的工程对象。"
    return {"answer": answer, "trace": trace}


if __name__ == "__main__":
    question = "为什么 Agent 需要 Harness?"
    print("Naive answer:")
    print(naive_research(question))
    print("\nHarnessed run:")
    print(json.dumps(harnessed_research(question), ensure_ascii=False, indent=2))
