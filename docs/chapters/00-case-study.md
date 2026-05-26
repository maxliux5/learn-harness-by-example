# 00 案例导读：一次失败如何暴露 Harness 的必要性

如果这套教程只能讲清楚一个观点，我希望是这个：Agent Harness 的价值，不是让一次 demo 更好看，而是让一次失败变得可解释、可复现、可改进。

这一章先不介绍接口，也不讲目录结构。我们直接看一个研究助手的失败：它给出了一段听起来正确的答案，甚至能通过关键词 Eval，但 Trace 证明它根本没有查资料。

## 失败现场

用户任务是：

```text
解释 agent harness 的作用，必须基于资料回答
```

一个 naive Agent 可能回答：

```text
Agent Harness 包含运行、观察、评测和复现，但这句话没有任何资料证据。
```

这句话有几个危险特征：它包含核心术语，语气稳定，读起来也不像胡说。但用户要求的是“基于资料回答”，而不是“把正确词汇排成一句话”。

如果系统只保存最终答案，你只能争论这句话好不好。如果系统保存 Trace，你可以问一个更硬的问题：它到底有没有调用工具拿资料？

## 为什么关键词 Eval 会被骗

早期 Eval 常常从关键词检查开始，例如要求答案包含：

- `运行`
- `观察`
- `评测`
- `复现`

这类检查很便宜，也很透明，适合防明显回归。但它有一个天然漏洞：模型可以在没有任何证据的情况下，把这些词都说出来。

本仓库里有一个专门的场景叫 `eval_false_positive`。运行：

```bash
python3 examples/ch00_case_study.py
```

你会看到同一段回答在 keyword-only eval 里通过，但在 evidence eval 里失败。差别不在文风，而在 Trace：

```json
{
  "keyword_only_passed": true,
  "evidence_eval_passed": false,
  "missing_trace": ["tool.called", "tool.returned"]
}
```

这就是 Harness 的第一层深度：它把“答案像不像对”拆成“文本是否满足要求”和“行为路径是否满足要求”。

## Trace 给出的诊断

失败运行的 Trace 大致是：

```text
run.started
model.called
model.returned
run.completed
```

这里缺了两个关键事件：

```text
tool.called
tool.returned
```

这说明模型没有走外部资料路径，而是直接生成最终答案。此时最应该改的，不一定是答案模板，而可能是工具选择策略、prompt 约束、终止条件，或者 Eval 规则。

没有 Trace 时，团队很容易陷入“再调一版 prompt 看看”。有 Trace 时，问题变得具体：这个 run 没有证据链。

## 修复后的行为

同一个任务在 `happy_path` 场景里会变成：

```text
run.started
model.called
model.returned
tool.called
tool.returned
model.called
model.returned
run.completed
```

最终答案也会明确说明它基于资料：

```text
基于资料：... Agent Harness 让 Agent 可运行、可观察、可评测、可复现。
```

这不是因为答案更长了，而是因为运行路径变了：Agent 先请求工具，工具返回资料，模型再基于工具结果生成最终答案。

一个好的 Harness 应该能同时回答两类问题：

- 用户看最终答案：它是否清楚、有依据？
- 工程师看运行记录：它是否真的走了预期路径？

## Replay 为什么重要

修复一次失败以后，还要避免它下次回来。Replay 的作用，是把 baseline 和 improved 放在同一份可比较的记录里。

本章脚本会输出一段 compare 结果：

```json
{
  "answer_changed": true,
  "tool_call_delta": 1,
  "completed_delta": 0
}
```

这段对比的意义是：答案变了，工具调用增加了，run 仍然正常完成。它比“我感觉新版好一点”更适合进入 code review、issue 讨论和发布说明。

脚本也会把报告保存为 [`traces/case-study-report.json`](../traces/case-study-report.json)。这份 artifact 很适合放在 issue 或 PR 里讨论，因为它同时包含 false positive、improved run 和 replay compare。

## 这条主线如何贯穿 10 章

后面的 10 章会把这次失败拆开讲：

| 章节 | 解决的问题 |
| --- | --- |
| 01-02 | 为什么需要固定 `Agent.run(task)` |
| 03 | 为什么模型 Provider 要可替换 |
| 04 | 如何把工具调用变成结构化行为 |
| 05 | 如何保存一次 run 的状态 |
| 06 | 如何把过程记录成 Trace |
| 07 | 如何写可重复 Eval |
| 08 | 如何把失败变成 failure case |
| 09 | 如何保存并比较 run record |
| 10 | 如何整理成可复制的最小项目 |

如果你只想快速判断这套教程有没有用，可以先读本章，再运行：

```bash
python3 -m harness diagnose
python3 -m unittest discover tests
```

`diagnose` 会跑完整 failure corpus。它覆盖无工具调用、参数错误、空工具结果、编造来源、循环、schema drift、provider timeout 和 eval false positive。

## Checkpoint

读完本章，你应该记住三件事：

- 一个漂亮答案可能没有证据链。
- 一个关键词 Eval 可能被漂亮答案骗过。
- Harness 的价值，是把最终文本、行为路径、失败诊断和版本对比放进同一个工程反馈回路。

接下来从第 01 章开始，我们会把这个反馈回路从零搭出来。
