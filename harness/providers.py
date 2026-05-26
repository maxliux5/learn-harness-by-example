"""Optional real model providers for the tutorial harness."""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from typing import Callable


Transport = Callable[[dict], dict]


class MiniMaxModelClient:
    """OpenAI-compatible MiniMax provider with a tool-first research policy.

    The default tutorial path stays deterministic through ScenarioModel. This
    provider is for the real smoke test: it asks the harness to collect local
    evidence first, then calls MiniMax to synthesize the final answer.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "MiniMax-M2.7",
        base_url: str = "https://api.minimax.io/v1",
        timeout: float = 60.0,
        transport: Transport | None = None,
        tool_query: str = "agent harness",
        retries: int = 1,
    ) -> None:
        if not api_key:
            raise ValueError("MiniMax API key is required")
        self.api_key = api_key
        self.model = model
        self.base_url = self._normalize_base_url(base_url)
        self.timeout = timeout
        self.transport = transport or self._http_transport
        self.tool_query = tool_query
        self.retries = retries

    @classmethod
    def from_env(
        cls,
        model: str | None = None,
        base_url: str | None = None,
        timeout: float | None = None,
        transport: Transport | None = None,
    ) -> "MiniMaxModelClient":
        api_key = os.environ.get("MINIMAX_API_KEY") or os.environ.get("MINIMAX_KEY")
        if not api_key:
            raise RuntimeError("Set MINIMAX_API_KEY before using the MiniMax provider")
        return cls(
            api_key=api_key,
            model=model or os.environ.get("MINIMAX_MODEL", "MiniMax-M2.7"),
            base_url=base_url or os.environ.get("MINIMAX_BASE_URL") or os.environ.get("MINIMAX_API_HOST", "https://api.minimax.io/v1"),
            timeout=timeout if timeout is not None else float(os.environ.get("MINIMAX_TIMEOUT", "60")),
            transport=transport,
            retries=int(os.environ.get("MINIMAX_RETRIES", "1")),
        )

    def complete(self, messages: list[dict]) -> dict:
        tool_messages = [message for message in messages if message.get("role") == "tool"]
        if not tool_messages:
            return {"type": "tool_call", "tool": "search", "args": {"query": self.tool_query}}

        request = {
            "api_key": self.api_key,
            "base_url": self.base_url,
            "model": self.model,
            "messages": self._chat_messages(messages, tool_messages[-1]),
            "temperature": 0.2,
            "max_tokens": 500,
            "timeout": self.timeout,
        }
        raw = self._send_with_retries(request)
        content = self._extract_content(raw)
        return {
            "type": "final",
            "content": content,
            "raw": {
                "provider": "minimax",
                "model": self.model,
                "usage": raw.get("usage", {}),
            },
        }

    def _chat_messages(self, messages: list[dict], tool_message: dict) -> list[dict]:
        task = next((str(message.get("content", "")) for message in messages if message.get("role") == "user"), "")
        evidence = str(tool_message.get("content", ""))
        return [
            {
                "role": "system",
                "content": (
                    "你是一个严谨的研究助手。只能基于提供的资料回答。"
                    "答案必须以“基于资料：”开头，并简短说明运行、观察、评测、复现。"
                ),
            },
            {
                "role": "user",
                "content": f"任务：{task}\n\n资料：{evidence}",
            },
        ]

    def _http_transport(self, request: dict) -> dict:
        payload = {
            "model": request["model"],
            "messages": request["messages"],
            "temperature": request["temperature"],
            "max_tokens": request["max_tokens"],
            "stream": False,
        }
        http_request = urllib.request.Request(
            url=f"{request['base_url']}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {request['api_key']}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(http_request, timeout=float(request["timeout"])) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"MiniMax HTTP {exc.code}: {body}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"MiniMax request failed: {exc.reason}") from exc

    def _send_with_retries(self, request: dict) -> dict:
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                request["attempt"] = attempt + 1
                return self.transport(request)
            except (TimeoutError, RuntimeError, urllib.error.URLError) as exc:
                last_error = exc
                if attempt >= self.retries:
                    raise
        raise RuntimeError(f"MiniMax request failed: {last_error}")

    def _extract_content(self, raw: dict) -> str:
        choices = raw.get("choices", [])
        if not choices:
            raise RuntimeError(f"MiniMax response has no choices: {raw}")
        message = choices[0].get("message", {})
        content = message.get("content", "")
        if isinstance(content, list):
            content = "".join(str(part.get("text", part)) if isinstance(part, dict) else str(part) for part in content)
        if not content:
            raise RuntimeError(f"MiniMax response has empty content: {raw}")
        return re.sub(r"(?is)<think>.*?</think>\s*", "", str(content)).strip()

    def _normalize_base_url(self, base_url: str) -> str:
        normalized = base_url.rstrip("/")
        if normalized.endswith("/chat/completions"):
            normalized = normalized[: -len("/chat/completions")]
        if not normalized.endswith("/v1"):
            normalized = f"{normalized}/v1"
        return normalized
