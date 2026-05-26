# Roadmap

Status tracker for the public tutorial. Each chapter should have a runnable command, an inspectable output, and a concrete artifact a reader can keep.

**Legend:** ✅ complete · 🚧 in progress · ⬚ planned

Total estimated time: ~6.5 hours.

| # | Chapter | Status | Est. | Proof command | Ships |
| --- | --- | --- | --- | --- | --- |
| 00 | Failure case study | ✅ | ~25 min | `python3 examples/ch00_case_study.py` | `traces/case-study-report.json` |
| 01 | Why Agent needs Harness | ✅ | ~30 min | `python3 examples/ch01_why_harness.py` | minimal trace shape |
| 02 | Minimal Agent Loop | ✅ | ~35 min | `python3 examples/ch02_minimal_loop.py` | `Agent.run(task)` |
| 03 | Model Provider boundary | ✅ | ~35 min | `python3 examples/ch03_model_provider.py` | `ModelClient` protocol idea |
| 04 | Tools | ✅ | ~40 min | `python3 examples/ch04_tools.py` | tool call / return events |
| 05 | RunState | ✅ | ~35 min | `python3 examples/ch05_run_state.py` | run state object |
| 06 | Trace and observability | ✅ | ~45 min | `python3 examples/ch06_trace_observability.py` | structured trace event schema |
| 07 | Eval | ✅ | ~45 min | `python3 examples/ch07_eval.py` | eval report |
| 08 | Failure-driven improvement | ✅ | ~45 min | `python3 examples/ch08_failure_driven.py` | failure checks |
| 09 | Replay and comparison | ✅ | ~40 min | `python3 examples/ch09_replay_compare.py` | baseline / improved records |
| 10 | Minimal Harness project | ✅ | ~55 min | `python3 examples/ch10_research_harness.py` | `harness/` package and CLI |

## Course-Wide Checks

Run these before publishing a change:

```bash
python3 -m unittest discover tests
for file in examples/ch*.py; do python3 "$file" >/tmp/learn_harness_example.out || exit 1; done
python3 -m harness diagnose
python3 -m harness eval
node --check docs/assets/site.js
```

## Next Depth Upgrades

These are deliberately not required for the current v1, but they are the most valuable follow-ups:

| Upgrade | Why it would matter |
| --- | --- |
| Optional OpenAI-compatible provider | Shows the same harness boundary with a real model |
| More realistic search corpus | Makes tool evidence less toy-like |
| Trace viewer page | Lets readers inspect events without opening raw JSON |
| Per-chapter exercises | Helps readers prove understanding |
| More replay comparisons | Shows prompt/model/tool regressions side by side |
