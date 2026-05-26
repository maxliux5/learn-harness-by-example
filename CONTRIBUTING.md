# Contributing

欢迎贡献章节修订、示例改进和更多 eval case。

## 贡献方向

- 修正教程中的概念错误或表述不清
- 增加更小、更容易运行的 Python 示例
- 补充 trace、eval、replay 相关案例
- 改进 GitHub Pages 阅读体验
- 增加可复用 outputs，例如 prompt、skill、trace artifact 或 eval case

新增章节请先看 [CHAPTER_TEMPLATE.md](CHAPTER_TEMPLATE.md)，并把章节状态同步到 [ROADMAP.md](ROADMAP.md)。

## 本地检查

提交前建议运行：

```bash
for file in examples/ch*.py; do python3 "$file"; done
python3 -m unittest discover tests
python3 -m harness diagnose
node --check docs/assets/site.js
python3 -m http.server 8000
```

然后在浏览器打开 `http://127.0.0.1:8000/docs/` 检查页面。

## 内容风格

- 中文讲解为主，必要英文术语保留原文。
- 先给可运行例子，再抽象概念。
- 每章保持一个明确问题、一个可检查信号和一个 checkpoint。
- 避免引入非标准库依赖，除非章节明确需要。
- 如果答案质量是重点，也要解释 trace 或 eval 如何证明它。
