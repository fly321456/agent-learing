# 06 Session And Reliability

模块 6 的独立离线快照，覆盖 Session/Turn 标识、UTF-8 持久化、上下文预算、摘要边界、Checkpoint 恢复、副作用去重、配置校验和分类重试。

```powershell
python demo.py
python steps/l21_session_turn_run.py
python steps/l22_context_budget.py
python steps/l23_checkpoint_resume.py
python steps/l24_retry_config.py
```

Demo 预期包含 `context_trimmed=true side_effects=1 attempts=2 result=recovered`。该快照不依赖网络，也不会修改真实仓库。
