# 10 整理成一个最小 Harness 项目

前 9 章分别搭出了 Agent Loop、Provider、Tool、RunState、Trace、Eval、失败驱动和 Replay。最后一章不继续堆功能，而是把这些概念放到同一个最小项目里，帮助你看清楚它们如何协作。

本章的目标不是交付生产级框架，而是给你一个可以带走的骨架：面对自己的业务 Agent 时，你知道每类代码应该放在哪一层，也知道失败时该从哪里开始查。

## 学习目标

本章要整合一条端到端研究助手流程：

- 用 `ResearchAgent.run(task)` 作为统一入口。
- 通过 `ModelClient` 替换模型 Provider。
- 注册并调用 `Tool`。
- 返回包含 messages、Trace、final answer 和 errors 的 `RunState`。
- 用 `EvalCase` 检查固定任务。
- 把一次最终运行保存成 run record artifact。
- 看清楚后续扩展应该进入哪一层。

完成本章后，你应该能把前面章节的零件组织成一个最小 harness。

## 本章问题

真实项目可能会拆成多个模块：

```text
agent/
  core.py
  state.py
providers/
  mock.py
tools/
  search.py
evals/
  cases.py
traces/
  sample-run.jsonl
```

前面章节仍然保留 `examples/ch*.py` 作为逐章教学脚本；真正可复制的最终骨架放在 `harness/` 包里：

```bash
python3 -m harness run --scenario happy_path
python3 -m harness diagnose
python3 -m unittest discover tests
```

第 10 章对应的 [`examples/ch10_research_harness.py`](../examples/ch10_research_harness.py) 现在只是一个薄入口：它导入 `harness/` 里的组件，跑一次完整流程，并保存 run record。

## 模块边界

读 `harness/` 目录时，建议按职责理解：

| 组件 | 职责 | 不应该负责 |
| --- | --- | --- |
| `TraceEvent` | 描述一条时间线事件 | 决定 Agent 策略 |
| `RunState` | 保存一次 run 的状态 | 保存长期记忆或全局配置 |
| `Tool` | 描述可调用外部能力 | 决定什么时候调用自己 |
| `EvalCase` | 描述固定评测任务 | 修改 Agent 行为 |
| `ModelClient` | 定义模型调用协议 | 绑定具体 SDK 到 Agent |
| `ResearchAgent` | 编排模型、工具、状态和 Trace | 实现具体搜索数据源 |
| `search` | 查询本地知识库 | 记录全局评测结果 |
| `evaluate_run` | 跑单个 case 并输出报告 | 改写 Agent 主流程 |
| `save_run_record` | 保存一次 run 的证据包 | 重新执行模型调用 |

对应文件大致是：`harness/core.py` 管 loop，`harness/models.py` 管 deterministic model doubles，`harness/tools.py` 管工具，`harness/eval.py` 管规则，`harness/replay.py` 管 run record，`harness/failures.py` 管 failure corpus。

这个边界能防住“所有代码都塞进一个大函数”的问题。文件可以先小，职责不能混。

## 运行示例

运行：

```bash
python3 examples/ch10_research_harness.py
```

输出分四段：

1. `ANSWER`：研究助手最终答案。
2. `TRACE`：逐行打印的 Trace event。
3. `EVAL`：两条 `EvalCase` 的 pass/fail 报告。
4. `RECORD`：保存到 `traces/final/latest-run.json` 的 run record 路径。

请重点观察一次完整运行的路径：

- `ResearchAgent.run` 创建 `RunState`。
- 记录 `run.started`。
- 调用 `MockResearchModel`。
- 模型先返回 `tool_call`。
- Agent 查找并执行 `search`。
- 工具结果进入 messages。
- 模型基于资料返回 `final`。
- Agent 设置 `state.final_answer`，记录 `run.completed`。

这条路径就是前面 9 章的合并版。

你也可以直接运行可复用 CLI：

```bash
python3 -m harness run --scenario happy_path
python3 -m harness run --scenario eval_false_positive --no-save
python3 -m harness diagnose
```

第二条命令故意制造一个 false positive：答案包含关键词，但没有工具证据。它说明为什么第 07 章的关键词 Eval 只是起点，最终还需要 Trace assertion。

如果你想把这个仓库当成自己的 starter project，可以用 editable install 暴露一个本地命令：

```bash
python3 -m pip install -e .
learn-harness diagnose
learn-harness run --scenario happy_path
```

`pyproject.toml` 只注册了一个很薄的入口，真正逻辑仍然在 `harness/` 包里。这样做的好处是：读教程时可以直接跑 `python3 -m harness`，迁移到自己项目时也可以拥有一个正式 CLI。

如果你已经设置了 MiniMax key，也可以跑真实 provider：

```bash
export MINIMAX_API_KEY=...
python3 -m harness run --provider minimax --model MiniMax-M2.7 --output traces/minimax/latest-run.json
python3 examples/minimax_smoke.py
```

真实 provider 仍然遵守同一个 harness 结构：Agent 先记录 `tool.called` / `tool.returned`，再把本地资料交给 MiniMax 生成最终答案。这样真实模型试跑也能被 Trace 和 Eval 检查。

如果网络较慢，可以设置：

```bash
export MINIMAX_TIMEOUT=90
export MINIMAX_RETRIES=2
```

## 观察与改进

最终示例已经具备一个最小 Agent Harness 的骨架：

- 可运行：统一入口是 `ResearchAgent.run(task)`。
- 可替换：模型通过 `ModelClient` 协议接入。
- 可扩展：工具通过 `Tool` 注册。
- 可观察：关键步骤写入 `state.trace`。
- 可检查：`evaluate` 用固定 cases 跑回归。
- 可复盘：`save_run_record` 会把配置、task、answer、errors、Trace 和 Eval report 写成 artifact。

它能防住的不是所有生产问题，而是最早最常见的工程混乱：

- 不知道 Agent 到底有没有查资料。
- 不知道最终答案来自哪一步。
- 不知道改动是否破坏固定任务。
- 不知道模型、工具和状态的职责边界。

如果要继续扩展，建议按层添加，而不是随手堆代码：

- 真实 Provider：新增一个实现 `ModelClient.complete` 的类。
- 更多 Tool：新增 `Tool(...)` 注册项，保持 handler 输入输出结构化。
- 更强 Trace：给事件增加 run id、step、duration、error code。
- 更强 Eval：保存 per-case Trace，加入人工评分或模型辅助评分。
- Replay 存储：把当前 JSON artifact 扩展为 JSONL、SQLite 或对象存储。

## Ship It

本章带走的 artifact 是完整的最小 harness package：

```text
harness/
├── core.py
├── models.py
├── providers.py
├── tools.py
├── state.py
├── eval.py
├── replay.py
└── failures.py
```

它不是生产框架，但已经具备 fork 价值：你可以保留接口边界，替换 Provider、Tool、EvalCase 和存储方式。`providers.py` 展示了如何把真实 MiniMax API 接进同一个 `ModelClient` 协议。真正的课程终点不是“看懂一篇文章”，而是拿到一个能迁移到自己 agent 项目的工程骨架。

## Exercises

1. 把 `MiniMaxModelClient` 的默认 model 改成另一个 MiniMax 模型，但不要改 `ResearchAgent.run`。
2. 给 `TraceEvent` 增加 `duration_ms`，并思考哪些事件能自然记录耗时。
3. 用 [`outputs/skill-agent-harness-reviewer.md`](../outputs/skill-agent-harness-reviewer.md) 审查你自己的 agent 项目，列出最缺的两个 Trace event。

## 常见误区

- 看到最终结构后立刻抽象成通用框架，反而让学习成本变高。
- 把 Eval 当成额外脚本，而不是 harness 的核心反馈回路。
- 把 Trace 只当 debug 输出，没有保存为可复用 artifact。
- 在 Provider、Tool、Agent 之间互相调用，导致职责边界失效。
- 只关注最终答案质量，不检查工具证据、状态和版本记录。

## Checkpoint

读完整套教程后，你应该能独立回答：

- Agent Harness 要解决什么工程问题？
- 为什么 Agent Loop、Provider、Tool、RunState、Trace、Eval 和 Replay 要分开设计？
- 如何从一次失败案例出发，写出可重复检查？
- 如何通过 Trace 判断失败发生在哪一层？
- 如何保存和比较不同版本的 Agent 行为？

这套教程刻意保持示例小，是为了让你先掌握结构。下一步把它带到自己的业务场景时，优先保留这些边界，再按需要替换 Provider、Tool、Eval 和存储方式。
