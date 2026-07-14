# 04 Runtime Refactor

模块 4 的独立标准包快照。它把模块 3 的单文件 Agent 拆为 Agent 配置、LLM 边界、Tool 边界和 Runner，并明确区分 `LLMResponse`、`ToolResult` 与 `RunResult`。

```powershell
python demo.py
python steps/l13_agent_configuration.py
python steps/l14_llm_response.py
python steps/l15_tool_manager.py
python steps/l16_runner_results.py
```

预期 Demo 输出包含：`content=42 steps=2 tools=1` 和 `finish_reason=completed`。

源码位于 `src/course_runtime/`，只表示“学完模块 4”时的能力，不依赖最终 `agent_from_scratch` 包。模块 5 才加入工作区、审批、超时和 Coding Tools。
