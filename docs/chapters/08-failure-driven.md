# 08 失败案例驱动改进

Agent 开发很容易陷入一个循环：看到输出不好，就改 prompt；改完再跑一个例子；看起来好了，就继续。这个流程的问题是没有固定失败，也没有固定判断标准。下一次改动可能又把同样的问题带回来。

失败案例驱动改进的意思是：先把失败描述清楚，再把它变成可重复检查，最后用 Trace 和 Eval 验证修复是否真的解决目标问题。

## 学习目标

本章要把失败变成可执行的改进任务：

- 描述具体失败，而不是泛泛说“效果不好”。
- 用 Trace 判断失败发生在模型、Tool、State、Stop rule 还是 Eval。
- 用 `EvalCase` 和检查函数固定失败，防止后续回归。
- 理解 baseline 和 improved 对比的价值。

完成本章后，你应该能把一次糟糕输出转化为一个可以复跑的工程 case。

## 本章问题

研究助手常见失败包括：

- 用户要求基于资料回答，但模型没有调用 Tool。
- Tool 返回了资料，但最终答案没有引用。
- Tool 参数错误，查不到结果。
- Agent 循环太久，或者过早结束。
- 答案格式漂移，破坏下游解析。

本章模拟一个具体失败：用户明确要求“必须基于资料回答”，baseline 却直接给出结论，没有使用任何工具证据。

失败描述应该包含三部分：

| 部分 | 示例 |
| --- | --- |
| 输入任务 | `解释 harness 的作用，必须基于资料回答` |
| 实际输出 | `Harness 很重要，因为它让 Agent 更可靠。` |
| 不合格原因 | Trace 中没有 `name="tool.called"`，答案也没有证据标记 |

只有这样，失败才可以被复现和修复。

## 失败拆解

读 [`examples/ch08_failure_driven.py`](../examples/ch08_failure_driven.py) 时，先看 `Run`：

```python
@dataclass
class Run:
    version: str
    answer: str
    trace: list[dict] = field(default_factory=list)
```

这个结构比前几章更简化，但它保留了对比所需的核心字段：版本、答案、Trace。

再看两个版本：

- `baseline_agent`：Trace 里只有 `run.started` 和 `model.final`，并标注 `answered without evidence`。
- `improved_agent`：Trace 里出现 `tool.called`、`tool.returned`，最终答案以“基于搜索结果”开头。

本章的修复目标不是“让答案更长”，也不是“让文风更好”，而是满足一个明确要求：回答必须有工具证据。

## 运行示例

运行：

```bash
python3 examples/ch08_failure_driven.py
```

输出报告里有两类信息：

- `checks`：每个版本是否通过 `evaluate_run(case, run)`。
- `runs`：baseline 和 improved 的答案与 Trace。

请重点看 `EvalCase` 和 `evaluate_run(case, run)` 的组合：

```python
case = EvalCase(
    name="must answer with tool evidence",
    task="解释 harness 的作用，必须基于资料回答",
    requires_tool=True,
    required_answer_terms=["基于", "资料"],
)
used_tool = any(event["name"] == "tool.called" for event in run.trace)
missing_terms = [term for term in case.required_answer_terms if term not in run.answer]
```

这个检查同时看行为路径和最终文本。只看文本可能被漂亮话骗过；只看 Trace 可能忽略答案没有引用证据。两者合起来，才更接近用户要求。

## 观察与改进

本章能防住的错误，是“把所有问题都归因于 prompt”。同一个失败可以来自不同层：

| 失败来源 | Trace 里可能看到什么 | 改进方向 |
| --- | --- | --- |
| Prompt / 模型策略 | 没有 `tool.called` | 要求先查资料，或调整工具选择策略 |
| Tool | 有 `tool.called`，但结果为空 | 修正参数、数据源或错误处理 |
| State | 有工具结果，但没有进入 messages | 检查 RunState 更新和上下文拼接 |
| Stop rule | 过早 `run.completed` 或 max steps | 调整终止条件 |
| Eval | 明显不合格却通过 | 增加 Trace 级或答案级检查 |

可以尝试的小实验：

1. 删除 improved Trace 里的 `name="tool.called"` 事件，观察检查是否失败。
2. 保留 `tool.called`，但把答案改成不包含“基于”或“资料”，观察另一个条件是否失败。
3. 给检查函数增加 `tool.returned` 要求，防止只记录调用、不检查结果。

这些实验会让你看到：失败驱动不是写更多测试，而是把真实问题翻译成最小可验证条件。

本仓库还把这个思路扩展成了一组 failure corpus：[`cases/failure_corpus.json`](../cases/failure_corpus.json)。里面包含无工具调用、错误工具参数、空工具结果、编造来源、循环、schema drift、provider timeout、eval false positive 等案例。运行：

```bash
python3 -m harness diagnose
```

你会得到 `detected/total` 报告。这里的 detected 不是说失败通过了，而是说 harness 成功抓住了这个失败信号。

## Ship It

本章带走的 artifact 是 failure case 的写法：

```json
{
  "task": "...",
  "expected_diagnosis": "...",
  "eval": {
    "trace_must_include": ["tool.called"],
    "required_terms": ["基于"]
  }
}
```

它的价值是把一次失败从聊天记录里提炼出来，变成可以长期复跑的工程资产。`cases/failure_corpus.json` 就是这个思想的集合版。

## Exercises

1. 给 `cases/failure_corpus.json` 增加一个“工具返回过期资料”的 case。
2. 把 `eval_false_positive` 的规则改弱，观察它为什么可能不再被抓住。
3. 使用 [`outputs/prompt-failure-to-eval.md`](../outputs/prompt-failure-to-eval.md) 把一次失败描述改写成 EvalCase。

## 常见误区

- 看到失败后立刻改 prompt，没有把失败写成 case。
- 修复后只看一个新输出，没有和 baseline 对比。
- 把所有失败都怪模型，不检查 Tool、RunState、Trace 和终止条件。
- 检查只看最终答案，不看行为路径，导致“看起来像基于资料”的回答蒙混过关。

## Checkpoint

本章结束时，你应该能说明：

- 一个好的失败样本应该包含哪些信息。
- 为什么 baseline 和 improved 要放在同一份报告里对比。
- Trace 如何帮助定位失败来源。
- 如何把失败转化成可重复的检查函数或 Eval case。

下一章会把运行记录保存成 Run Record，并比较不同版本的答案、工具调用和分数变化。
