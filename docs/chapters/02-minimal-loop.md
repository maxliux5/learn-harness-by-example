# 02 第一个最小 Agent Loop

Agent Loop 是 harness 的心脏。它把用户任务变成模型输入，接收模型输出，再决定是否继续。真实 Agent 可能会多轮调用模型、调用工具、修正状态、检查终止条件，但学习时不应该一开始就把这些都塞进来。

本章先写一个只有一次模型调用的最小 loop。它看起来简单，但非常重要：从这里开始，外部调用方只需要认识 `Agent.run(task)`，后续 Provider、Tool、RunState、Trace 和 Eval 都会围绕这个入口扩展。

## 学习目标

本章要完成一个小而稳定的运行入口：

- 理解 `Agent.run(task)` 为什么是 harness 的公共边界。
- 看清楚 task 如何被包装成 `messages`。
- 使用 mock model 保持示例可重复，不被真实 API、网络和随机输出干扰。
- 为下一章抽象 `ModelClient` 留出位置。

完成本章后，你不需要拥有完整 Agent，只需要拥有一个能被继续扩展的 Agent Loop。

## 本章问题

我们希望调用方写的是：

```python
answer = agent.run("解释 agent harness 的作用")
```

而不是让调用方手动处理这些内部细节：

- 如何构造 messages。
- 如何调用模型。
- 如何从 response 中取出最终文本。
- 将来要不要记录 Trace、更新 RunState、检查工具调用。

本章最小流程只有三步：

1. 把用户任务包装成 `{"role": "user", "content": task}`。
2. 调用 `self.model.complete(messages)`。
3. 返回 `response["content"]`。

这个 loop 还没有工具，也没有多轮控制，但它已经把“运行一次 Agent”的边界收拢到了一个方法里。

## Loop 的边界

读 [`examples/ch02_minimal_loop.py`](../examples/ch02_minimal_loop.py) 时，重点看 `Agent` 类：

```python
class Agent:
    def __init__(self, model: MockModelClient) -> None:
        self.model = model

    def run(self, task: str) -> str:
        messages = [{"role": "user", "content": task}]
        response = self.model.complete(messages)
        return response["content"]
```

这里有两个边界值得留意：

| 边界 | 现在做什么 | 以后会扩展什么 |
| --- | --- | --- |
| `Agent.run` | 接收 task，返回 answer | 返回 `RunState`，记录 Trace，处理工具循环 |
| `model.complete` | 接收 messages，返回 content | 抽象为 Provider，支持不同模型和调试实现 |

这就是 harness 的早期设计原则：先把稳定接口立住，再逐章扩展接口背后的行为。

## 运行示例

运行：

```bash
python3 examples/ch02_minimal_loop.py
```

输出会是一句由 `MockModelClient` 生成的固定回答。请不要把 mock 当成“偷懒”。在教程早期，mock 的价值很明确：

- 每次运行都能得到可预测输出。
- 读者不用准备 API key。
- 章节重点集中在 loop，而不是鉴权、网络、限流或模型版本。

如果你想确认 loop 真的在传递 task，可以修改 `agent.run(...)` 里的文本，观察输出是否包含新的任务内容。

## 观察与改进

本章最值得观察的是 `messages`。它只有一条 user message，却已经采用了常见聊天模型的结构：

```python
[{"role": "user", "content": task}]
```

这个结构会在后面继续增长：

- 第 04 章会追加 `role="tool"` 的工具结果。
- 第 05 章会把 messages 放进 `RunState`。
- 第 06 章会记录模型调用前后的 Trace event。
- 第 10 章会把所有能力整合到一个研究助手 harness。

这个最小 loop 现在能防住一个常见错误：把 prompt 拼接、模型调用和结果处理散落在业务函数里。一旦散落，后面想加 Trace 或 Eval 时就要到处改；收敛到 `Agent.run` 后，新增能力会有明确位置。

可以尝试的小改动：

1. 在 `run()` 里临时 `print(messages)`，观察模型实际收到的数据结构。
2. 给 `MockModelClient.complete` 增加一个 `raw` 字段，再思考 `Agent.run` 是否应该暴露它。
3. 把返回值改成 dict，感受为什么第 05 章需要正式引入 `RunState`。

## Ship It

本章带走的 artifact 是第一个稳定入口：

```python
answer = agent.run(task)
```

它看起来很小，但这是后面所有能力的挂载点。Provider 替换、Tool 调度、RunState、Trace、Eval 和 Replay 都不会要求调用方改成另一套入口。一个好的 harness 先把外部 API 固定下来，再慢慢丰富内部行为。

## Exercises

1. 给 `Agent.run` 增加 `system_message` 参数，再判断这会不会污染公共入口。
2. 让 `MockModelClient` 返回 dict 而不是字符串，思考返回值契约应该由谁定义。
3. 写一个第二个调用方函数，只依赖 `agent.run(task)`，验证调用方不需要理解 Provider 细节。

## 常见误区

- 一开始就接真实模型 API，结果学习 Agent Loop 时被环境问题打断。
- 把 prompt、provider、工具、评测和状态都写进一个函数，后续无法拆开演进。
- 让 `run()` 返回临时格式，调用方开始依赖内部细节，之后很难重构。
- 忽略 `messages` 的结构，直接拼字符串，导致工具结果和多轮上下文难以表达。

## Checkpoint

本章结束时，你应该能说明：

- `Agent.run(task)` 为什么是 harness 的第一个稳定入口。
- mock model 为什么能提升教程和测试的可重复性。
- 最小 Agent Loop 和完整 Agent Harness 之间还缺哪些层。

下一章会把 `MockModelClient` 抽象成 `ModelClient` / Provider，让同一个 Agent Loop 可以替换不同模型实现。
