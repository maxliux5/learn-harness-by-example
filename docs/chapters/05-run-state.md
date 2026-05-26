# 05 管理一次运行的 RunState

当 Agent 开始调用 Tool 后，运行过程里的信息会快速变多：用户任务、messages、工具请求、工具结果、最终答案、错误、终止原因。如果这些信息散落在局部变量和 print 里，失败时很难复盘。

`RunState` 的目标，是把“一次 run 的当前事实”集中到一个结构化对象里。它不是长期记忆，也不是数据库模型；它只描述这一次运行发生了什么。

## 学习目标

本章要把 Agent 的返回值从字符串升级为状态对象：

- 使用 `RunState` 保存 task、messages、tool calls、final answer 和 errors。
- 理解为什么结构化状态比日志字符串更适合后续 Eval 和 Replay。
- 区分单次运行状态和长期记忆，避免过早把所有东西塞进一个对象。
- 为下一章 Trace event 提供数据基础。

学完后，你应该能判断：某个字段应该进入 `RunState`，还是应该留在配置、Provider 或外部存储中。

## 本章问题

上一章的 `Agent.run()` 只返回最终字符串：

```python
answer = agent.run(task)
```

这对用户展示够用，但对工程调试不够。我们至少还想知道：

- 这次 task 是什么？
- 模型看过哪些 messages？
- 调用了哪些工具，参数和结果是什么？
- 有没有错误？
- 最终答案是在第几步得到的？

本章的最小结构是：

```python
@dataclass
class RunState:
    task: str
    messages: list[dict] = field(default_factory=list)
    tool_calls: list[dict] = field(default_factory=list)
    final_answer: str | None = None
    errors: list[str] = field(default_factory=list)
```

这个对象让“运行结果”不再只是一个文本，而是一份可检查的状态快照。

## 状态边界

读 [`examples/ch05_run_state.py`](../examples/ch05_run_state.py) 时，重点看 `RunState` 的字段选择。

| 字段 | 保存什么 | 不保存什么 |
| --- | --- | --- |
| `task` | 本次用户输入 | 用户画像、历史会话 |
| `messages` | 本次模型上下文 | 全局 prompt 仓库 |
| `tool_calls` | 本次工具调用记录 | 工具注册表本身 |
| `final_answer` | 本次最终答案 | 多版本答案历史 |
| `errors` | 本次运行错误 | 全局异常监控配置 |

这个边界能防住一种常见膨胀：看到状态对象后，把所有配置、缓存、用户记忆都塞进去。`RunState` 应该保持轻量、可序列化、和单次 run 绑定。

后面如果需要长期记忆，可以单独设计 Memory；如果需要保存多次运行，可以设计 Run Record；不要让 `RunState` 变成万能容器。

## 运行示例

运行：

```bash
python3 examples/ch05_run_state.py
```

输出是一份 JSON，包含这次运行的完整状态。请重点看三个位置：

- `messages`：先有 user message，再有 tool message，最后有 assistant message。
- `tool_calls`：记录 `tool`、`args` 和 `result`。
- `final_answer`：最终答案不再是唯一返回值，而是状态对象中的一个字段。

示例里使用：

```python
print(json.dumps(asdict(run), ensure_ascii=False, indent=2))
```

`asdict(run)` 能工作，说明 `RunState` 里的字段都是容易序列化的普通数据。这对后面的 Trace、Eval artifact 和 Replay 都很重要。

## 观察与改进

本章最值得观察的是 Agent Loop 对 `state` 的更新方式：

```python
state.messages.append(...)
state.tool_calls.append(...)
state.final_answer = ...
state.errors.append(...)
```

这些更新点就是未来插入 Trace event 的位置。例如：

- append user message 后，可以记录 `run.started`。
- 调用模型前后，可以记录 `model.called` / `model.returned`。
- 工具调用前后，可以记录 `tool.called` / `tool.returned`。
- 设置 `final_answer` 时，可以记录 `run.completed`。

`RunState` 能防住的核心错误，是“失败时只剩一段错误文本”。如果工具名未知，示例会把错误写进 `state.errors`，并继续让最终返回值保持结构化。这样调用方可以选择展示错误、保存状态、或交给 Eval 分析。

可以尝试的小实验：

1. 把 `MockModel` 返回的工具名改成未知工具，观察 `errors` 如何变化。
2. 删除 `state.messages.append({"role": "assistant", ...})`，思考 Replay 时会缺少什么。
3. 给 `RunState` 增加 `steps: int`，观察它和 Trace event 的职责差异。

## 常见误区

- 只保存最终答案，导致失败时没有排查线索。
- 把不可序列化对象放进状态，例如函数、SDK client、打开的文件句柄。
- 在状态里混入全局配置，让单次运行记录变得难以复现。
- 把 `RunState` 当长期记忆，导致一次 run 和跨 run 数据混在一起。

## Checkpoint

本章结束时，你应该能说明：

- `RunState` 为什么比单个字符串返回值更适合 harness。
- 哪些字段属于一次 run 的事实。
- 为什么可序列化是 `RunState` 的重要约束。
- Trace 和 RunState 的关系：一个是状态快照，一个会成为时间线。

下一章我们会把这些状态更新点变成结构化 Trace event，让运行过程可以按时间顺序复盘。
