# 07 从 Demo 走向 Eval

Demo 是“跑给人看”，Eval 是“每次改动都能重复检查”。Agent 项目最容易出问题的地方，不是第一次跑不出结果，而是后面不断改 prompt、换模型、加工具之后，没人能说清楚系统到底变好了还是变差了。

本章用一组很小的规则评测，把前面搭出的 Agent 行为固定下来。早期 Eval 不需要完美，它的价值是让团队拥有一个透明、可重复、能发现回归的比较基准。

## 学习目标

本章要建立第一组可重复检查：

- 定义 `EvalCase`，把任务和期望行为写成数据。
- 用固定 cases 重复运行 Agent。
- 用简单规则生成 pass/fail，而不是依赖主观感觉。
- 理解 early eval 的价值：先防明显回归，再逐步升级评分方法。

学完后，你应该能把“这个回答感觉不太对”转化为一个可执行的检查。

## 本章问题

研究助手的输出看起来合理，不代表它满足要求。比如用户问 “Explain trace”，我们可能至少希望答案包含：

- `Trace`
- `模型调用`
- `工具调用`

本章的最小 case 结构是：

```python
@dataclass
class EvalCase:
    name: str
    task: str
    required_terms: list[str]
    forbidden_terms: list[str] = field(default_factory=list)
```

评分规则也很朴素：运行 Agent，检查答案里是否包含 required terms，以及是否出现 forbidden terms。这个规则不够聪明，但非常透明。透明意味着失败时你知道为什么失败，也知道规则本身是否需要调整。

## Case 设计

读 [`examples/ch07_eval.py`](../examples/ch07_eval.py) 时，先看 `CASES`。它包含 5 个任务：

| Case | 检查重点 |
| --- | --- |
| `harness role` | 是否提到运行、观察、评测 |
| `demo vs eval` | 是否区分 Demo、eval 和回归 |
| `trace value` | 是否提到 Trace、模型调用、工具调用 |
| `provider abstraction` | 是否说明 Provider 可替换 |
| `replay value` | 是否提到 Replay、复现、对比 |

这些 case 都很小，因为 early eval 最重要的是定位清楚。一个 case 最好只检查一类行为；如果一个综合 case 同时检查格式、证据、工具、术语和安全规则，失败时你很难知道该改哪里。

这组 Eval 也承接了前面章节：它把 Harness、Provider、Trace、Replay 这些核心概念变成固定检查点。

## 运行示例

运行：

```bash
python3 examples/ch07_eval.py
```

你会看到一个报告：

- `passed`：通过的 case 数量。
- `total`：总 case 数量。
- `results`：每个 case 的结果、缺失词、禁用词和答案。

仓库里也提供了一个样例结果：

```text
traces/eval-results.json
```

请重点观察 `missing_terms`。它比单纯的总分更有教学价值，因为它告诉你失败原因：是没有提到 Trace，还是没有提到工具调用，还是完全没覆盖用户问题。

## 观察与改进

本章能防住的错误，是“改完只看一个顺眼样例”。有了 Eval 后，每次改 prompt、改 Provider 或改 Tool 策略，都可以重新跑同一组 cases，看是否出现回归。

但是也要看清楚限制：

- 关键词检查可能被“堆词”骗过。
- 它无法判断长答案是否真的有逻辑。
- 它不检查 Trace 里是否真的调用了工具。
- 它只适合做早期、低成本、透明的回归检查。

这不是缺点，而是阶段选择。本教程先用简单规则把 Eval 流程跑通，后续会把规则升级成 Trace assertion：

- 增加 golden answer 对比。
- 增加人工评分字段。
- 增加模型辅助评分，但保留评分理由。
- 增加 Trace 级检查，例如必须出现 `tool.called`。

仓库里的 `harness/eval.py` 已经给出了这个升级方向：`EvalCase` 不只包含 `required_terms` 和 `forbidden_terms`，还可以声明 `trace_must_include`、`trace_must_not_include` 和 `expected_error_terms`。这能抓住一种常见 false positive：答案里堆满关键词，但 Trace 证明它根本没有查资料。

可以尝试的小实验：

1. 删除 `SimpleResearchAgent` 某个答案里的关键词，观察对应 case 如何失败。
2. 给某个 case 增加新的 `forbidden_terms`，检查答案是否出现禁用词。
3. 把 Eval 报告保存成文件，思考第 09 章如何把它放进 Run Record。

## Ship It

本章带走的 artifact 是 Eval report：

```text
traces/eval-results.json
```

它把“我觉得不错”改成了可以复跑的检查结果。即使规则很朴素，也已经包含 case 名称、缺失词、禁用词和答案。这个报告未来会被 Run Record 收进去，成为版本对比的一部分。

## Exercises

1. 新增一个 case，要求答案同时解释 `RunState` 和 `Trace` 的区别。
2. 写一个会被关键词骗过的答案，然后给 case 增加 `trace_must_include` 规则。
3. 给 Eval report 增加 `eval_version`，思考历史结果如何保持可比。

## 常见误区

- 用一个很大的综合 case 检查所有能力，失败后无法定位。
- 频繁修改评分规则，却不记录版本，导致历史结果不可比。
- 只看总分，不读失败 case、missing terms 和 Trace。
- 把 Eval 当成上线前一次性检查，而不是日常开发反馈回路。

## Checkpoint

本章结束时，你应该能回答：

- Demo 和 Eval 的区别是什么。
- 为什么 early eval 可以简单，但必须稳定和透明。
- `EvalCase` 应该如何设计得小而明确。
- 什么时候应该升级到 Trace 级检查或人工评分。

下一章我们会故意固定一个失败案例，用 Trace 和 Eval 驱动改进，而不是靠随手改 prompt。
