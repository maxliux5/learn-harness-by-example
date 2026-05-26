# Learn Harness by Example

Build the debugging, eval, and replay shell every serious agent eventually needs.

很多 Agent demo 的问题不是“第一次跑不起来”，而是第二周开始没人说得清：这次有没有查工具、为什么答案变了、改 prompt 后到底更好还是更差。这个仓库用一个研究助手，从最小 `Agent.run(task)` 搭到可观察、可评测、可回放的 Agent Harness。

这不是一个大框架。它是一套可以复制的小骨架，帮你把 Agent 从“看起来能用”推进到“出了问题能查”。

## Start With The Failure

先运行这个案例：

```bash
python3 examples/ch00_case_study.py
```

它会制造一个很真实的 false positive：答案包含“运行、观察、评测、复现”，所以 keyword-only eval 会通过；但 Trace 里没有 `tool.called` 和 `tool.returned`，所以 evidence eval 会失败。

核心输出长这样：

```json
{
  "keyword_only_passed": true,
  "evidence_eval_passed": false,
  "missing_trace": ["tool.called", "tool.returned"]
}
```

这就是本教程的主线：**不要只评最终文本，也要评 Agent 是否真的走了预期行为路径。**

脚本会把完整报告写到 [traces/case-study-report.json](traces/case-study-report.json)，方便在 GitHub 上直接查看。

## What You Will Build

- 一个稳定的 `run(task)` 入口
- 可替换的 `ModelClient`
- 工具注册和错误处理
- `RunState` 和结构化 Trace
- 文本规则 + Trace assertion 的 Eval
- Baseline / improved 的 Replay artifact
- 一个可复制的 `harness/` Python package
- 一组失败语料：无工具调用、参数错误、空工具结果、编造来源、循环、schema drift、provider timeout、eval false positive

## Quickstart

所有代码只依赖 Python 标准库。

```bash
python3 examples/ch00_case_study.py
python3 -m harness run --scenario happy_path
python3 -m harness diagnose
python3 -m unittest discover tests
```

也可以安装成一个本地 CLI：

```bash
python3 -m pip install -e .
learn-harness diagnose
```

运行一个会失败的案例：

```bash
python3 -m harness run --scenario eval_false_positive --no-save
```

这个场景的答案包含“运行、观察、评测、复现”等关键词，但 Trace 里没有 `tool.called`。它用来说明：只靠关键词 Eval 很容易被漂亮话骗过。

## Failure Corpus

失败语料在 [cases/failure_corpus.json](cases/failure_corpus.json)。每个 case 都包含：

- `scenario`: 使用哪个 deterministic model double
- `task`: 用户任务
- `expected_diagnosis`: 应该从 Trace 里读出的诊断
- `eval`: 答案规则、Trace 规则、错误规则

示例：

```json
{
  "id": "hallucinated_citation",
  "title": "模型编造来源",
  "scenario": "hallucinated_citation",
  "expected_diagnosis": "答案像引用了来源，但 Trace 没有工具证据，应该用 trace assertion 抓住。"
}
```

`diagnose` 输出的是 `detected/total`，意思是 harness 是否抓住了这些失败，而不是失败场景本身是否“通过”。这组失败语料是本教程最重要的部分：Harness 的价值不是把 happy path 包漂亮，而是在 messy path 上留下证据。

仓库里提交了一份样例报告：[traces/failure-corpus-report.json](traces/failure-corpus-report.json)。

## Repository Map

```text
.
├── harness/               # 可复用的最小 Agent Harness skeleton
├── cases/                 # 失败语料和诊断规则
├── tests/                 # 标准库 unittest
├── docs/                  # GitHub Pages 教程站
├── examples/              # 每章对应的独立教学脚本
├── traces/                # 示例 trace/eval/replay 输出
├── pyproject.toml         # 可编辑安装和 learn-harness CLI
└── .github/workflows/     # GitHub Pages 自动部署
```

## Online Tutorial

发布到 GitHub Pages 后，阅读地址通常是：

```text
https://<your-github-username>.github.io/learn_harness_by_example/
```

本仓库上传整个项目到 Pages，因此教程页可以链接到 `examples/`、`cases/` 和 `traces/`。

本地预览：

```bash
python3 -m http.server 8000
```

然后打开：

```text
http://127.0.0.1:8000/docs/
```

## Chapters

0. 案例导读：一次失败如何暴露 Harness 的必要性
1. 为什么 Agent 需要 Harness
2. 第一个最小 Agent Loop
3. 把模型 Provider 抽象出来
4. 给 Agent 增加工具
5. 管理一次运行的状态
6. 加入 Trace 和可观测性
7. 从 Demo 走向 Eval
8. 失败案例驱动改进
9. Replay、对比和版本化
10. 整理成一个最小 Harness 项目

## Why This Might Be Worth A Star

如果你只是想看“怎么调一次 LLM API”，这里太重了。  
如果你已经遇到这些问题，它会比较有用：

- Agent 明明答了，但不知道是不是基于工具证据。
- 改 prompt 后感觉变好，却没有回归基准。
- Eval 总分变高，但 Trace 显示行为路径退化。
- 工具失败被最终答案掩盖。
- 想保存 run record，却不知道 state、trace、eval report 怎么分层。

这套教程的核心观点是：**Agent 工程化不是先追求更聪明的回答，而是先让每一次运行留下足够证据。**

## License

代码示例使用 MIT License。教程文本和图文内容使用 Creative Commons Attribution 4.0 International License。
