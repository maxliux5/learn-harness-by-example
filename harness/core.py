"""Core agent loop for the reusable tutorial harness."""

from __future__ import annotations

from .models import ModelClient, ScenarioModel
from .providers import MiniMaxModelClient
from .state import RunState
from .tools import Tool, default_tools


class ResearchAgent:
    def __init__(self, model: ModelClient, tools: list[Tool], max_steps: int = 4) -> None:
        self.model = model
        self.tools = {tool.name: tool for tool in tools}
        self.max_steps = max_steps

    def run(self, task: str) -> RunState:
        state = RunState(task=task)
        state.messages.append({"role": "user", "content": task})
        state.record("run.started", {"task": task})

        for step in range(self.max_steps):
            state.record("model.called", {"step": step, "message_count": len(state.messages)})
            try:
                response = self.model.complete(state.messages)
            except Exception as exc:
                error = f"Model error: {exc}"
                state.errors.append(error)
                state.record("model.failed", {"step": step, "error": str(exc)})
                return state

            response_type = response.get("type")
            state.record("model.returned", {"step": step, "response_type": response_type, "raw": response})

            if response_type == "final":
                state.final_answer = str(response.get("content", ""))
                state.messages.append({"role": "assistant", "content": state.final_answer})
                state.record("run.completed", {"answer": state.final_answer})
                return state

            if response_type != "tool_call":
                error = f"Invalid model response: missing supported type in {response}"
                state.errors.append(error)
                state.record("model.invalid_response", {"step": step, "response": response})
                return state

            tool_name = response.get("tool")
            args = response.get("args", {})
            if not isinstance(args, dict):
                args = {}

            tool = self.tools.get(str(tool_name))
            if tool is None:
                error = f"Unknown tool: {tool_name}"
                state.errors.append(error)
                state.record("tool.failed", {"tool": tool_name, "error": error})
                state.messages.append({"role": "tool", "name": str(tool_name), "content": error})
                continue

            state.record("tool.called", {"tool": tool.name, "args": args})
            try:
                result = tool.handler(args)
            except Exception as exc:
                result = {"content": f"工具调用失败：{exc}", "ok": False}
                state.errors.append(result["content"])
                state.record("tool.failed", {"tool": tool.name, "error": str(exc)})

            state.record("tool.returned", {"tool": tool.name, "result": result})
            if result.get("ok") is False:
                error = f"Tool {tool.name} returned no usable result: {result.get('content', '')}"
                state.errors.append(error)
                state.record("tool.unusable_result", {"tool": tool.name, "result": result})
            state.messages.append({"role": "tool", "name": tool.name, "content": result.get("content", "")})

        error = "Max steps exceeded"
        state.errors.append(error)
        state.record("run.failed", {"reason": "max_steps_exceeded"})
        return state


def build_agent(scenario: str = "happy_path", max_steps: int = 4, provider: str = "scenario", model: ModelClient | None = None) -> ResearchAgent:
    if model is None:
        if provider == "scenario":
            model = ScenarioModel(scenario=scenario)
        elif provider == "minimax":
            model = MiniMaxModelClient.from_env()
        else:
            raise ValueError(f"Unknown provider: {provider}")
    return ResearchAgent(model=model, tools=default_tools(), max_steps=max_steps)
