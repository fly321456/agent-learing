# Multi-Agent Course Lab

完全离线的多 Agent 工程实验：可拆分性审计、Planner/Executor 协议、共享状态与局部失败、最小 Reviewer 和单 Agent 基线比较。

```powershell
python demo.py
python steps/a01_decomposability_audit.py
python steps/a02_protocols.py
python steps/a03_shared_state_failures.py
python steps/a04_reviewer_comparison.py
```

只有存在固定评测并观察到质量增益时才建议多 Agent；没有增益时保留更便宜、可调试的单 Agent。
