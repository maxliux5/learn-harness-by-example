# 04 给 Agent 增加 Tool

一个研究助手如果只能依赖模型内部知识，很容易过时、编造，或者在用户要求“必须基于资料回答”时仍然直接给结论。Tool 让 Agent 可以访问外部能力：搜索、读文档、查数据库、执行代码、调用业务 API。

本章不会实现完整的 function calling 协议，而是先把 Tool 进入 harness 的路径讲清楚：模型提出工具调用意图，Agent Loop 查找并执行 Tool，把结果放回 messages，模型再基于工具结果生成最终答案。

## 学习目标

本章要让 Agent 从“单次模型回答”升级成“能协调模型和工具”：

- 定义最小 `Tool` 结构：`name`、`description`、`handler`。
- 理解模型如何返回结构化 `tool_call`。
- 看清楚工具结果如何变成 `role="tool"` 的 message。
- 学会把工具不存在、参数不对、没有结果这类失败纳入 harness，而不是让流程悄悄失控。

完成本章后，Agent Loop 不再只是“问模型一次”，而是开始承担调度职责。

## 本章问题

我们希望工具注册长这样：

```python
Tool(
    name="search",
    description="Search local knowledge base",
    handler=search,
)
```

模型返回的不是自由文本，而是一个动作：

```python
{"type": "tool_call", "tool": "search", "args": {"query": "harness"}}
```

Agent Loop 需要回答四个问题：

1. 这个工具名是否存在？
2. 参数应该交给哪个 handler？
3. 工具结果如何放回模型上下文？
4. 如果工具无法执行，应该如何留下可观察结果？

这四个问题就是 Tool 调度的最小协议。

## 工具协议

读 [`examples/ch04_tools.py`](../examples/ch04_tools.py) 时，先看 `Tool`：

```python
@dataclass
class Tool:
    name: str
    description: str
    handler: Callable[[dict], dict]
```

这个定义很小，但已经包含三个关键设计：

| 字段 | 作用 |
| --- | --- |
| `name` | 作为模型请求和工具注册表之间的稳定 ID |
| `description` | 给未来 prompt 或 tool schema 使用，说明工具能力 |
| `handler` | 真正执行外部能力，接收 dict 参数并返回 dict 结果 |

再看 `Agent.__init__`：

```python
self.tools = {tool.name: tool for tool in tools}
```

这里把工具列表变成 name 到 Tool 的映射。这个小动作很重要：Agent Loop 不应该用一堆 `if tool_name == ...` 判断所有工具。工具越多，注册表越能保持主流程清晰。

## 运行示例

运行：

```bash
python3 examples/ch04_tools.py
```

你会看到最终答案里包含“基于工具结果”。完整流程是：

1. 用户任务进入 messages。
2. `MockToolCallingModel` 第一次看到还没有 tool message，于是返回 `tool_call`。
3. Agent 根据 `response["tool"]` 找到 `search`。
4. `search` 从本地 `KnowledgeBase` 查询 `harness`。
5. Agent 追加一条 `{"role": "tool", "name": "search", "content": ...}`。
6. 模型第二次被调用，基于工具结果返回 `final`。

请特别观察循环：

```python
for _ in range(4):
```

这就是最早的停止保护。即使模型一直请求工具，harness 也不会无限循环。

## 观察与改进

本章能防住的第一个错误，是“模型声称基于资料，但流程里根本没有资料”。当工具结果以 `role="tool"` 进入 messages 后，后续 Trace 和 Eval 就有机会检查：这次回答之前到底有没有工具证据。

本章能防住的第二个错误，是“工具失败让程序直接崩掉”。示例里如果工具不存在，会追加一条 tool message：

```python
{"role": "tool", "content": "工具不存在：..."}
```

这还不是生产级错误处理，但它说明了一件事：工具失败也应该变成 harness 可见的事实。

可以尝试的小实验：

1. 把模型返回的 `"tool": "search"` 改成 `"tool": "lookup"`，观察 Agent 如何处理未知工具。
2. 把 query 改成不存在的词，观察 `search` 返回“没有找到相关资料。”后最终答案如何变化。
3. 把 `range(4)` 改成 `range(1)`，体会 max steps 为什么是 Agent Loop 的基本保护。

## 常见误区

- 把 Tool 当普通函数调用，不记录工具名、参数和结果，后续无法排查证据链。
- 让工具异常直接中断整个 run，Trace 和 RunState 都来不及保存。
- 工具返回一大段自由文本，没有结构化字段，Eval 很难检查行为是否符合预期。
- 把工具选择逻辑写死在业务代码里，导致新增工具时必须改 Agent 主流程。

## Checkpoint

本章结束时，你应该能解释：

- Tool 为什么需要 `name`、`description` 和 `handler`。
- `tool_call` response 和 `final` response 有什么区别。
- 工具结果为什么要回到 messages，而不是只存在局部变量里。
- max steps 能防住哪类 Agent Loop 问题。

下一章会把 task、messages、tool calls、final answer 和 errors 收进 `RunState`，让一次运行从“返回字符串”升级成“返回状态对象”。
