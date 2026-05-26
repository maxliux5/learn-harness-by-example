# 03 把模型 Provider 抽象出来

如果 Agent 直接依赖某个模型厂商的 SDK，后续会很难切换模型、比较实验结果，也很难在没有网络的环境下稳定测试。Provider 抽象要解决的不是“支持所有模型特性”，而是先把 Agent Loop 和底层模型实现分开。

本章会保留一个很小的接口：Agent 只知道它可以把 `messages` 发给 `model.complete()`，并得到一个至少包含 `content` 的 response。至于这个 model 是 mock、echo、真实 API，还是未来的 replay stub，都不应该影响 Agent 主流程。

## 学习目标

本章要把模型调用从 Agent 中拆出来：

- 定义最小 `ModelClient` 协议。
- 让 `MockModelClient` 和 `EchoModelClient` 共享同一个调用入口。
- 理解 Provider 的边界：翻译请求和响应，而不是决定 Agent 策略。
- 为后续 Eval、Replay 和真实 Provider 留出可替换位置。

学完后，你应该能判断：哪些代码属于 Agent Loop，哪些代码应该放进 Provider。

## 本章问题

上一章的 Agent 写法已经能跑，但类型上直接依赖 `MockModelClient`：

```python
class Agent:
    def __init__(self, model: MockModelClient) -> None:
        self.model = model
```

问题不在于 mock，而在于 Agent 对具体实现知道得太多。如果明天要换成真实模型，或者想用一个 debug provider 检查 messages，你不应该改 Agent 的主流程。

本章把依赖改成协议：

```python
class ModelClient(Protocol):
    def complete(self, messages: list[dict]) -> dict:
        """Return a response with at least a content field."""
```

只要对象实现了 `complete(messages) -> dict`，就可以成为 Provider。

## Provider 边界

Provider 的职责可以用一句话概括：把 harness 的通用消息格式翻译给模型，再把模型响应翻译回 harness 的通用格式。

它应该负责：

- 接收 `messages`。
- 调用或模拟模型。
- 返回 `{"content": "...", "raw": ...}` 这类通用结果。
- 保留必要的原始响应，方便 debug。

它不应该负责：

- 决定是否调用工具。
- 修改 Agent 的终止条件。
- 直接写 Eval 分数。
- 把 Trace event 散落在 Provider 内部，导致主流程看不见。

这个边界能防住一个非常常见的错误：为了快速接入某个 SDK，把 SDK response 直接传给业务层。短期很快，长期会让每一次切换模型都变成全局修改。

## 运行示例

运行：

```bash
python3 examples/ch03_model_provider.py
```

你会看到同一个 `Agent` 先后使用两个 Provider：

- `MockModelClient`：返回固定中文解释，并在 `raw` 中标记 provider label。
- `EchoModelClient`：把收到的 message 数量和最后一条内容回显出来。

读 [`examples/ch03_model_provider.py`](../examples/ch03_model_provider.py) 时，重点看 `Agent.run` 没有因为 provider 不同而变化：

```python
return self.model.complete(messages)["content"]
```

这就是 Provider 抽象的价值：Agent Loop 只依赖稳定协议，不依赖具体厂商或调试实现。

## 观察与改进

本章最值得观察的是 `EchoModelClient`。它不是为了生产使用，而是为了帮助你检查 harness 内部的数据流：

- Agent 有没有正确构造 messages？
- message 数量是否符合预期？
- 最后一条 content 是不是用户任务？

这种 debug provider 在真实项目里很有用。比如你怀疑 prompt 拼错了，可以临时换成 echo provider，而不是把真实模型调用和 print 混在一起。

可以尝试的小改动：

1. 给 `MockModelClient(label="mock-v2")` 传入不同 label，观察 `raw` 如何变化。
2. 让 `EchoModelClient` 返回完整 `messages`，思考为什么不应该直接把它展示给最终用户。
3. 在 response 中增加 `usage` 字段，思考它应该由 Provider 提供，还是由 Agent 计算。

这些改动会引出一个原则：Provider 可以暴露更多元数据，但 Agent 应该只依赖自己真正需要的稳定字段。

## Ship It

本章带走的 artifact 是 `ModelClient` 边界：

```python
class ModelClient(Protocol):
    def complete(self, messages: list[dict]) -> dict:
        ...
```

这个边界让教程后续可以一直使用 deterministic provider。它也让你在真实项目里先写 mock、echo、replay provider，再接真实 SDK。Provider 抽象的成熟标志不是支持最多厂商，而是 Agent Loop 不需要知道自己正在用哪个厂商。

仓库最终版已经包含一个真实 provider：`harness/providers.py` 里的 `MiniMaxModelClient`。它使用 MiniMax 的 OpenAI-compatible chat completions API，但仍然实现同一个 `complete(messages) -> dict` 协议。

## Exercises

1. 新增一个 `FailingModelClient`，让它抛出异常，观察当前章节是否能处理这个失败。
2. 新增 `usage` 字段，思考它应该进入 response、Trace，还是 Run Record。
3. 设置 `MINIMAX_API_KEY`，运行 `python3 -m harness run --provider minimax --model MiniMax-M2.7`，观察真实 provider 的 Trace 是否仍然保留工具证据。

## 常见误区

- Provider 抽象过早追求完整，第一版就塞进 streaming、tool calling、token usage 和所有厂商差异。
- Agent 直接读取 SDK 原始 response，导致切换 Provider 时主流程到处报错。
- mock provider 带随机行为，Eval 和 Replay 失去可重复性。
- 把工具策略写进 Provider，让模型调用层和 Agent 控制层纠缠在一起。

## Checkpoint

本章结束时，你应该能做到：

- 解释 `ModelClient` / Provider 为什么是 Agent Loop 外的一层边界。
- 用同一个 `Agent` 替换 mock provider 和 debug provider。
- 说清楚 response 中 `content` 和 `raw` 的不同用途。

下一章会让模型不只返回最终文本，还能请求 Tool 调用。Provider 抽象会继续留在模型层，工具调度则进入 Agent Loop。
