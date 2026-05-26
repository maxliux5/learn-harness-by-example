"""State and trace primitives for one agent run."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class TraceEvent:
    name: str
    payload: dict
    timestamp: str = field(default_factory=utc_now)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class RunState:
    task: str
    messages: list[dict] = field(default_factory=list)
    trace: list[TraceEvent] = field(default_factory=list)
    final_answer: str | None = None
    errors: list[str] = field(default_factory=list)

    def record(self, name: str, payload: dict | None = None) -> None:
        self.trace.append(TraceEvent(name=name, payload=payload or {}))

    def trace_names(self) -> list[str]:
        return [event.name for event in self.trace]

    def to_dict(self) -> dict:
        return {
            "task": self.task,
            "messages": self.messages,
            "trace": [event.to_dict() for event in self.trace],
            "final_answer": self.final_answer,
            "errors": self.errors,
        }

