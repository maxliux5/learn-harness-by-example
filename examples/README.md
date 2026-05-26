# Examples

这些示例对应教程的 10 个正文章节，外加一个 `ch00_case_study.py` 案例导读。所有脚本都只依赖 Python 标准库。

运行单章：

```bash
python3 examples/ch00_case_study.py
python3 examples/ch04_tools.py
```

运行全部：

```bash
for file in examples/ch*.py; do python3 "$file"; done
```

每个脚本都保持较小规模，重点是展示当前章节新增的 harness 能力，而不是实现完整生产框架。

第 10 章之后，推荐直接看可复用骨架：

```bash
python3 -m harness run --scenario happy_path
python3 -m harness diagnose
python3 -m unittest discover tests
```

如果你设置了 `MINIMAX_API_KEY`，可以跑真实 provider smoke test：

```bash
python3 -m harness run --provider minimax --model MiniMax-M2.7 --output traces/minimax/latest-run.json
python3 examples/minimax_smoke.py
```

如果网络较慢，可以临时设置 `MINIMAX_TIMEOUT=90` 或 `MINIMAX_RETRIES=2`。
