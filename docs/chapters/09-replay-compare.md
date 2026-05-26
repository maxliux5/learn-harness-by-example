# 09 Replay、对比和版本化

当你开始频繁改 prompt、Provider、Tool 策略和 Eval 规则，单次输出就不够用了。你需要知道：同一个任务，在不同版本下，答案、工具调用、Trace 和分数分别发生了什么变化。

Replay 和 compare 是 harness 的实验工作台。它们不只是为了“保存日志”，而是为了让每次 Agent 改动都有证据可查。

## 学习目标

本章要让运行结果可以被保存和比较：

- 定义最小 Run Record，保存配置、task、answer、Trace 和 score。
- 记录 `agent_version` 和 `provider`，避免结果来源不清。
- 对比两个版本的答案变化、工具调用变化和分数变化。
- 理解 Replay 与 Eval、Trace、RunState 的关系。

学完后，你应该能把“这次好像变好了”改写成“这些字段显示它在哪些方面变了”。

## 本章问题

我们需要保存一次 run 的证据包：

```python
run_record = {
    "config": {"agent_version": "baseline", "provider": "mock"},
    "task": "...",
    "answer": "...",
    "trace": [...],
    "score": 0.8,
}
```

这个结构回答了四个问题：

- 怎么跑的：`config`
- 跑了什么：`task`
- 怎么得到结果：`trace`
- 结果如何：`answer` 和 `score`

如果没有这些字段，未来看到一个答案时就很难判断：它来自哪个版本，是否用了同一个模型，是否真的调用了工具，是否比旧版本分数更高。

## Run Record

读 [`examples/ch09_replay_compare.py`](../examples/ch09_replay_compare.py) 时，先看 `make_record`。它用参数构造一份最小记录：

```python
def make_record(version: str, answer: str, tool_calls: int, score: float) -> dict:
    return {
        "config": {"agent_version": version, "provider": "mock", "eval_version": "rules-v1"},
        "task": "...",
        "answer": answer,
        "trace": [...],
        "score": score,
    }
```

这里的 Trace 是简化版本，但仍然沿用 `name`、`payload`、`timestamp` 事件形态，并保留了 `name="tool.called"` 事件，所以可以统计工具调用次数。示例随后会调用 `save_record` 把 baseline 和 improved 写入 `traces/replay/`，再用 `load_record` 读回来比较。也就是说，本章的 Replay 不是只在内存里比较，而是先形成可保存的 run artifact。

Run Record 和前面概念的关系是：

| 概念 | 在 Run Record 中的角色 |
| --- | --- |
| RunState | 提供 task、answer、errors 等状态字段 |
| Trace | 提供行为路径 |
| Eval | 提供 score 或 per-case 结果 |
| Provider | 进入 config，说明模型来源 |
| Version | 进入 config，说明 prompt/策略版本 |

Run Record 是这些信息的打包方式。

## 运行示例

运行：

```bash
python3 examples/ch09_replay_compare.py
```

你会看到 baseline 和 improved 的差异摘要：

- `answer_changed`
- `score_delta`
- `tool_call_delta`
- `left_version`
- `right_version`

示例中的 improved 比 baseline 多 1 次工具调用，分数也从 0.4 提升到 1.0。这不是在证明 improved 永远更好，而是在证明：针对这一个固定任务和评分规则，它的行为发生了可解释变化。

运行后还会生成两份文件：

```text
traces/replay/baseline.json
traces/replay/improved.json
```

这两份文件就是本章的最小 Replay artifact。

## 观察与改进

本章能防住的错误，是“只保存最终答案”。如果只保存答案，你最多知道文本变了；如果保存 Run Record，你还能知道：

- 是哪个版本生成的答案。
- 使用了哪个 provider。
- 工具调用次数是否变化。
- 分数变化是否和行为变化一致。
- 是否出现新的错误事件。

`compare(left, right)` 现在只做三个对比，真实项目可以继续扩展：

- 对比 `errors` 数量。
- 对比 Trace 事件序列。
- 对比 token usage 或耗时。
- 对比每个 EvalCase 的 pass/fail。
- 对比输出格式是否符合 schema。

可以尝试的小实验：

1. 把 improved 的 `tool_calls` 改成 0，但保留高分，思考 compare 是否应该警告“分数和行为不一致”。
2. 给 record 增加 `eval_version`，说明评分规则来自哪个版本。
3. 给 trace 增加 `tool.returned`，比较两个版本是否拿到不同资料。

## 常见误区

- 只保存最终答案，导致无法解释为什么分数变化。
- 没有记录 provider、agent version、eval version，历史结果不可比。
- 只比较总分，不比较 Trace，错过行为路径退化。
- 把 Replay 当成“重新调用模型”，却没有保存当时配置和输入，导致复现条件不完整。

## Checkpoint

本章结束时，你应该能说明：

- Run Record 为什么不是普通日志。
- 一次可比较的 run 至少应该保存哪些字段。
- `score_delta` 和 `tool_call_delta` 分别能说明什么，不能说明什么。
- 为什么版本化 prompt、Provider 和 Eval 规则很重要。

下一章会把 Agent Loop、Provider、Tool、RunState、Trace、Eval 和 Replay 思想整理成一个最小完整 harness 项目。
