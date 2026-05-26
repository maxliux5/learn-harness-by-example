"""Chapter 09: compare saved run records."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


RECORD_DIR = Path("traces/replay")


def trace_event(name: str, payload: dict | None = None) -> dict:
    return {
        "name": name,
        "payload": payload or {},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def make_record(version: str, answer: str, tool_calls: int, score: float) -> dict:
    return {
        "config": {"agent_version": version, "provider": "mock", "eval_version": "rules-v1"},
        "task": "解释 harness 的作用，必须基于资料回答",
        "answer": answer,
        "trace": [
            trace_event("run.started"),
            *[trace_event("tool.called", {"tool": "search"}) for _ in range(tool_calls)],
            trace_event("run.completed"),
        ],
        "score": score,
    }


def save_record(record: dict) -> Path:
    RECORD_DIR.mkdir(parents=True, exist_ok=True)
    path = RECORD_DIR / f"{record['config']['agent_version']}.json"
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def load_record(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def compare(left: dict, right: dict) -> dict:
    return {
        "left_version": left["config"]["agent_version"],
        "right_version": right["config"]["agent_version"],
        "answer_changed": left["answer"] != right["answer"],
        "score_delta": round(right["score"] - left["score"], 2),
        "tool_call_delta": count_tool_calls(right) - count_tool_calls(left),
    }


def count_tool_calls(record: dict) -> int:
    return sum(1 for event in record["trace"] if event["name"] == "tool.called")


if __name__ == "__main__":
    baseline = make_record("baseline", "Harness 让 Agent 更可靠。", tool_calls=0, score=0.4)
    improved = make_record(
        "improved",
        "基于资料：Harness 负责运行、观察、评测和复现 Agent 行为。",
        tool_calls=1,
        score=1.0,
    )
    baseline_path = save_record(baseline)
    improved_path = save_record(improved)
    loaded_baseline = load_record(baseline_path)
    loaded_improved = load_record(improved_path)
    print(json.dumps(compare(loaded_baseline, loaded_improved), ensure_ascii=False, indent=2))
