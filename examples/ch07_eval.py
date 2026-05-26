"""Chapter 07: run a tiny eval suite."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field


@dataclass
class EvalCase:
    name: str
    task: str
    required_terms: list[str]
    forbidden_terms: list[str] = field(default_factory=list)


class SimpleResearchAgent:
    def run(self, task: str) -> str:
        answers = {
            "harness": "Agent Harness 负责运行、观察、评测和复现 Agent 行为。",
            "demo": "Demo 是单次展示，eval 是固定任务和评分规则，用来发现回归。",
            "trace": "Trace 是结构化事件流，记录模型调用、工具调用和错误。",
            "provider": "Provider 抽象让 harness 可以替换 mock 或真实模型。",
            "replay": "Replay 保存任务、配置、答案和 trace，用来复现与对比。",
        }
        for keyword, answer in answers.items():
            if keyword in task.lower():
                return answer
        return "没有足够信息。"


def evaluate(agent: SimpleResearchAgent, cases: list[EvalCase]) -> dict:
    results = []
    for case in cases:
        answer = agent.run(case.task)
        missing = [term for term in case.required_terms if term not in answer]
        forbidden = [term for term in case.forbidden_terms if term in answer]
        results.append(
            {
                "name": case.name,
                "passed": not missing and not forbidden,
                "missing_terms": missing,
                "forbidden_terms": forbidden,
                "answer": answer,
            }
        )

    passed = sum(1 for result in results if result["passed"])
    return {"passed": passed, "total": len(cases), "results": results}


CASES = [
    EvalCase("harness role", "Explain harness", ["运行", "观察", "评测"], ["魔法"]),
    EvalCase("demo vs eval", "Explain demo and eval", ["Demo", "eval", "回归"]),
    EvalCase("trace value", "Explain trace", ["Trace", "模型调用", "工具调用"]),
    EvalCase("provider abstraction", "Explain provider", ["Provider", "替换"]),
    EvalCase("replay value", "Explain replay", ["Replay", "复现", "对比"]),
]


if __name__ == "__main__":
    report = evaluate(SimpleResearchAgent(), CASES)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print("\nCases:")
    print(json.dumps([asdict(case) for case in CASES], ensure_ascii=False, indent=2))
