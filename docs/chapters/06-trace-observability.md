# 06 加入 Trace 和可观测性

`RunState` 像一次运行结束后的状态快照，Trace 则像运行过程中的时间线。只看最终状态，你知道“最后是什么”；看 Trace，你能知道“每一步什么时候发生、输入是什么、输出是什么、哪一步失败”。

Agent 一旦开始调用 Tool，Trace 就不再是可有可无的 debug 输出。没有 Trace，你只能看到最终答案错了；有 Trace，你可以判断问题发生在模型选择、工具执行、消息拼接、终止条件，还是 Eval 规则。

## 学习目标

本章要把运行过程变成事件流：

- 定义最小 `TraceEvent`：`name`、`payload`、`timestamp`。
- 在模型调用和工具调用前后记录事件。
- 使用 JSONL 输出 Trace，便于保存、追加和脚本分析。
- 区分 Trace 与普通日志、RunState 的职责。

完成本章后，你应该能通过 Trace 还原一次 Agent 运行的关键路径。

## 本章问题

我们需要回答的问题不再只是“最后答案是什么”，而是：

- run 从什么时候开始？
- 模型被调用了几次？
- 每次模型调用时 messages 有多少条？
- 模型返回的是 `tool_call` 还是 `final`？
- Tool 参数是什么，结果是什么？
- run 是正常完成，还是因为 max steps 失败？

最小事件结构如下：

```python
@dataclass
class TraceEvent:
    name: str
    payload: dict
    timestamp: str
```

事件名描述发生了什么，时间戳描述发生顺序，payload 保存排查需要的结构化信息。

## 事件设计

读 [`examples/ch06_trace_observability.py`](../examples/ch06_trace_observability.py) 时，先看 `TraceRecorder`：

```python
class TraceRecorder:
    def __init__(self) -> None:
        self.events: list[TraceEvent] = []

    def record(self, name: str, payload: dict) -> None:
        ...
```

这个 recorder 很小，但它建立了两个好习惯：

- 事件通过统一入口记录，而不是到处拼 print。
- 事件 payload 是 dict，后续可以被 Eval、Replay 或分析脚本读取。

本章示例记录了这些事件：

| 事件 | 说明 |
| --- | --- |
| `run.started` | 收到 task，运行开始 |
| `model.called` | 即将调用模型，记录 step 和 message_count |
| `model.returned` | 模型返回，记录 response_type |
| `tool.called` | 即将调用工具，记录工具名和参数 |
| `tool.returned` | 工具返回，记录结果 |
| `run.completed` | 得到最终答案 |
| `run.failed` | 超过最大步数 |

这些事件不追求完整，但已经覆盖了 Agent Loop 的主要决策点。

## 运行示例

运行：

```bash
python3 examples/ch06_trace_observability.py
```

你会先看到最终答案，然后看到 `TRACE JSONL`。JSONL 的特点是一行一个 JSON 对象，适合追加写入，也方便命令行工具逐行处理。仓库里也有一个样例：

```text
traces/sample-run.jsonl
```

请重点观察 `model.called` 和 `model.returned` 成对出现，`tool.called` 和 `tool.returned` 也成对出现。这样的事件对能帮助你定位“调用前正常，调用后异常”的边界。

## 观察与改进

Trace 能防住的核心错误，是“最终答案错了，但不知道错在哪”。例如：

- 如果没有 `tool.called`，说明模型没有请求工具，或 Agent 没有执行工具策略。
- 如果有 `tool.called` 但没有 `tool.returned`，问题可能在工具 handler。
- 如果 `tool.returned` 正常，但最终答案没引用工具结果，问题可能在 messages 拼接或模型策略。
- 如果连续出现很多 `model.called`，需要检查终止条件和 max steps。

payload 不应该无脑保存全部上下文。过大的 Trace 会难以阅读，也可能泄露敏感数据。教程里只记录 `message_count`、`response_type`、工具参数和结果摘要，是为了让 Trace 既可用又克制。

可以尝试的小实验：

1. 在 `tool.returned` 的 payload 中只保留 `result_length`，对比可读性和排查能力。
2. 给每个事件增加 `step` 字段，观察排序是否更清晰。
3. 把 `to_jsonl()` 的输出保存到文件，再思考 Replay 需要哪些额外元数据。

## Ship It

本章带走的 artifact 是 JSONL Trace：

```text
traces/sample-run.jsonl
```

一行一个事件的格式让 Trace 更像机器可读的证据，而不是给人看的散文日志。后面 failure corpus、trace assertion 和 replay compare 都依赖事件名稳定、payload 可解析。

## Exercises

1. 用 `rg 'tool.called' traces/sample-run.jsonl` 检查样例 Trace 是否真的调用了工具。
2. 给 `model.called` 增加 `provider` 字段，思考这会不会和 Run Record 的 `config.provider` 重复。
3. 故意让工具抛错，并设计应该出现 `tool.failed` 还是只有 `run.failed`。

## 常见误区

- 只在失败时记录 Trace，导致成功样本无法作为对比基准。
- 把 Trace 写成纯文本日志，后续脚本无法稳定解析。
- 在 payload 中保存过多敏感输入，发布样例时泄露数据。
- 事件名随意变化，导致 Eval 和 Replay 无法依赖稳定协议。

## Checkpoint

本章结束时，你应该能说明：

- Trace 与普通日志的区别。
- Trace 与 RunState 的区别。
- 为什么模型调用和工具调用都应该记录前后事件。
- JSONL 为什么适合作为早期 Trace artifact。

下一章会在固定任务上重复运行 Agent，用 Eval 判断改动有没有造成回归。
