"""Tool registry and local research tools."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass
class Tool:
    name: str
    description: str
    handler: Callable[[dict], dict]


KNOWLEDGE_BASE = {
    "agent harness": "Agent Harness 负责运行、约束、观察、评测和复现 Agent 行为。",
    "trace": "Trace 是一次运行的结构化事件时间线。",
    "eval": "Eval 是固定任务、评分规则和回归检查的组合。",
    "empty": "",
}


def search(args: dict) -> dict:
    if not isinstance(args, dict):
        return {"content": "工具参数错误：args 必须是 dict。", "ok": False}
    if "query" not in args:
        return {"content": "工具参数错误：缺少 query。", "ok": False}

    query = str(args.get("query", "")).lower()
    if query not in KNOWLEDGE_BASE:
        return {"content": "没有找到相关资料。", "ok": False}

    content = KNOWLEDGE_BASE[query]
    return {"content": content, "ok": bool(content)}


def default_tools() -> list[Tool]:
    return [Tool(name="search", description="Search local knowledge base", handler=search)]
