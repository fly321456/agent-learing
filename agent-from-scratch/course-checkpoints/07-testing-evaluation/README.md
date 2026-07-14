# 07 Testing, Evaluation And Observability

模块 7 的独立离线快照，覆盖 FakeLLM、Event 契约、临时 Git 仓库 E2E、20 个固定任务的动态指标与 JSONL Trace。

```powershell
python demo.py
python steps/l25_fake_llm.py
python steps/l26_contract_e2e.py
python steps/l27_twenty_case_eval.py
python steps/l28_jsonl_trace.py
```

Demo 预期包含 `total=20 passed=20 tool_calls=25 steps=40 trace_events=2`。将任一 case 的实际 Tool 序列改错，成功率必须下降，证明指标不是静态打印。
