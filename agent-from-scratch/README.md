# agent-from-scratch

一个小型、可检查、可离线测试的 Coding Agent Runtime，也是 8 模块 32 课深入浅出课程的唯一主项目。

课程现已改为 8 模块 32 课的深入浅出教学主线。`course-checkpoints/` 提供 starter 和 8 个模块完成态；学习者在被忽略的 `.learning/current/` 中逐课实践，`src/agent_from_scratch/` 保留为最终工程参考答案。

## 当前能力

- `BaseLLM.generate(...) -> LLMResponse` 隔离模型供应商。
- `Runner.run(...) -> RunResult` 返回完整内容、事件、工具结果和结束原因。
- 支持纯文本、单/多 Tool、未知 Tool、审批拒绝和 `max_steps`。
- 文件读取、搜索和补丁限制在解析后的工作区内；写入、执行以及未分类工具默认请求审批。
- 严格 Tool Schema 与本地参数复验；显式归一化 incomplete、failed、cancelled 和 refusal。
- Typed Session/Turn、显式上下文裁剪结果、已完成 call_id 恢复复用、模型 Retry、命令 Timeout 和脱敏 JSONL Trace。
- 20 个固定任务的协议重放与独立结果评测接口、真实工具 E2E 测试、CLI 和可选只读 MCP server。

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

写文件、执行命令或调用未明确分类的扩展工具时，CLI 会在 stderr 显示经过脱敏和截断的参数，并等待人工审批；EOF、空输入和审批异常都按拒绝处理。常用参数：

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

`LLMResponse` 只代表一次模型调用，`RunResult` 才代表完整 Agent 运行。Runner 不读取供应商 `raw_response.output`；续写数据经 `continuation_items` 不透明传递。适配层保留供应商状态详情和 refusal，不能把非 completed 状态伪装成正常文本完成。

## 安全边界

- 路径解析后必须仍位于 `ToolContext.workspace`；搜索会逐个复核 glob 候选的真实路径。
- 读取、搜索结果、单行和命令 Observation 均有服务端上限，模型参数不能放大上限。
- 补丁使用非空精确文本匹配，歧义默认失败，保留原换行并通过同目录临时文件原子替换。
- 命令接收 argv 数组并使用 `shell=False`，工作目录受限且有超时；这不是进程、网络或系统调用沙箱。
- 写入、执行及未分类工具默认拒绝，除非审批回调明确允许。
- Trace、Runner Event 和审批预览统一脱敏并限制大小；命令超时、审批拒绝和执行错误使用不同状态。

这些应用层限制不能替代容器、虚拟机、低权限用户和网络隔离。Checkpoint 通过持久化已完成 `call_id` 降低恢复时重复副作用，但 JSON 文件无法提供事务型 exactly-once；外部写操作仍需幂等键或事务设施。不要对不可信仓库授予主机高权限。

## MCP 实验

```powershell
coding-agent-mcp
```

MCP server 只暴露读取和搜索工具，复用主项目实现。stdio 模式下不要向 stdout 输出调试日志。

## 协议依据

- [OpenAI Function calling：严格模式](https://developers.openai.com/api/docs/guides/function-calling#strict-mode)
- [OpenAI Responses create：状态与输出类型](https://developers.openai.com/api/reference/resources/responses/methods/create)
- [MCP Python SDK v1](https://github.com/modelcontextprotocol/python-sdk/tree/v1.x)

依赖锁定在 `mcp>=1.27,<2`，因为本课程代码基于稳定的 v1 API；升级 v2 必须单独完成迁移和契约复测。

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
