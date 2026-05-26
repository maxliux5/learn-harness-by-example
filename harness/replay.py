"""Run record helpers for replay and comparison."""

from __future__ import annotations

import json
from pathlib import Path

from .state import RunState


def make_run_record(state: RunState, config: dict, eval_report: dict | None = None) -> dict:
    return {
        "config": config,
        "task": state.task,
        "answer": state.final_answer,
        "errors": state.errors,
        "trace": [event.to_dict() for event in state.trace],
        "eval_report": eval_report,
    }


def save_run_record(record: dict, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def load_run_record(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def compare_records(left: dict, right: dict) -> dict:
    return {
        "left_version": left["config"].get("agent_version"),
        "right_version": right["config"].get("agent_version"),
        "answer_changed": left.get("answer") != right.get("answer"),
        "left_errors": len(left.get("errors", [])),
        "right_errors": len(right.get("errors", [])),
        "tool_call_delta": count_events(right, "tool.called") - count_events(left, "tool.called"),
        "completed_delta": count_events(right, "run.completed") - count_events(left, "run.completed"),
    }


def count_events(record: dict, name: str) -> int:
    return sum(1 for event in record.get("trace", []) if event.get("name") == name)

