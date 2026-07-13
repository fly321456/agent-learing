# agent-from-scratch

一个小型、可检查、可离线测试的 Coding Agent Runtime，也是 M01-M08 课程的唯一主项目。

## 当前能力

- `BaseLLM.generate(...) -> LLMResponse` 隔离模型供应商。
- `Runner.run(...) -> RunResult` 返回完整内容、事件、工具结果和结束原因。
- 支持纯文本、单/多 Tool、未知 Tool、审批拒绝和 `max_steps`。
- Coding Tools 限制在工作区内，写入与执行默认请求审批。
- Session、上下文预算、检查点恢复、模型 Retry、命令 Timeout 和 JSONL Trace。
- 20 个固定任务的离线协议回归、真实工具 E2E 测试、CLI 和可选只读 MCP server。

## 安装

需要 Python 3.11 或更高版本。

```powershell
python -m pip install -e ".[dev]"
```

需要运行 MCP 实验时：

```powershell
python -m pip install -e ".[dev,mcp]"
```

## 离线验证

这些命令不需要 API Key：

```powershell
python -m pytest -q
python examples/offline_demo.py
coding-agent-eval
python -m compileall -q src tests examples
```

`coding-agent-eval` 使用脚本化 LLM 重放固定工具序列，验证 Runner 协议和指标管线，不代表真实模型成功率。在线模型效果需要单独记录模型、提示词、任务验收和费用。

## 使用真实模型

先显式配置密钥和模型。模型选择属于部署配置，不在仓库中声明永久默认值。

```powershell
$env:OPENAI_API_KEY="your-key"
$env:OPENAI_MODEL="your-model"
coding-agent --workspace . "检查这个项目并总结测试情况"
```

写文件或执行命令时，CLI 会在 stderr 显示工具与参数，并等待人工审批。常用参数：

```text
--workspace PATH   限定工具可访问的工作区
--max-steps N      限制模型轮次
--session ID       持久化多轮消息
--resume RUN_ID    从检查点恢复
--trace PATH       写入 JSONL 事件
--model NAME       覆盖 OPENAI_MODEL
```

## 架构

```text
CLI
 └─ Runner
     ├─ Agent 配置
     ├─ BaseLLM -> LLMResponse
     ├─ ToolManager -> ToolResult
     ├─ Event / RunResult
     ├─ Session / ContextWindow / CheckpointStore
     └─ RetryPolicy / JsonlTraceWriter
```

`LLMResponse` 只代表一次模型调用，`RunResult` 才代表完整 Agent 运行。Runner 不读取供应商 `raw_response.output`；续写数据经 `continuation_items` 不透明传递。

## 安全边界

- 路径解析后必须仍位于 `ToolContext.workspace`。
- 补丁使用精确文本替换，歧义匹配默认失败。
- 命令接收 argv 数组并使用 `shell=False`。
- 写入和执行风险工具默认拒绝，除非审批回调允许。
- 命令超时、审批拒绝和执行错误使用不同 `ToolResult.status`。

这些应用层限制不能替代容器、虚拟机、低权限用户和网络隔离。不要对不可信仓库授予主机高权限。

## MCP 实验

```powershell
coding-agent-mcp
```

MCP server 只暴露读取和搜索工具，复用主项目实现。stdio 模式下不要向 stdout 输出调试日志。

## 项目结构

```text
src/agent_from_scratch/  正式运行时包
tests/                   单元、契约、集成和 E2E 测试
evals/cases.json         20 个固定 Coding Agent 任务
examples/offline_demo.py 离线示例
history/                 历史练习快照
```

项目根目录的 `agent.py`、`runner.py` 等旧脚本已冻结，不是导入或运行入口。它们当前受企业 TSD/DLP 文件保护驱动影响，在安全策略解除前保留原位，避免 Git 将保护容器误当源码提交。

## 课程

从 [课程首页](../课程/README.md) 进入。每个里程碑都有对应源码、自动验证和面试答辩标准。
