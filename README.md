# Coding Agent Engineering Lab

这是一个用真实项目学习 Coding Agent 工程的仓库。课程不再以 56 节线性笔记为主，而是围绕 `agent-from-scratch` 的代码、测试、运行记录和答辩产物完成 8 个里程碑。

## 从这里开始

1. 阅读 [课程首页](课程/README.md)，按 M01-M08 顺序学习。
2. 进入 [agent-from-scratch](agent-from-scratch/README.md) 安装并运行项目。
3. 每个里程碑执行 `课程.md` 中的验证命令。
4. 使用对应 `验收与面试.md` 做代码讲解和设计答辩。

## 主项目能力

- 标准 `src/` Python 包与可选 OpenAI Responses API 适配器。
- 纯文本、单 Tool、多 Tool 和受控终止的 Agent Loop。
- 限定工作区的读取、搜索、精确补丁和命令工具。
- `LLMResponse`、`ToolResult`、`Event`、`RunResult` 分层协议。
- Session、上下文预算、检查点恢复、Retry、Timeout 和 JSONL Trace。
- 离线单元/契约/集成/E2E 测试与 20 个固定评测任务。
- CLI 必修入口和最小只读 MCP 选修实验。

## 快速验证

```powershell
cd agent-from-scratch
python -m pip install -e ".[dev,mcp]"
python -m pytest -q
python examples/offline_demo.py
coding-agent-eval
```

真实模型运行需要自行设置 `OPENAI_API_KEY` 和 `OPENAI_MODEL`，默认测试不访问网络或产生 API 费用。

## 仓库结构

```text
agent-from-scratch/
├── src/agent_from_scratch/   # 唯一运行时包
├── tests/                    # 离线测试
├── evals/                    # 20 个固定任务
├── examples/                 # 无密钥示例
└── pyproject.toml

课程/
├── 主线-Coding-Agent/        # M01-M08
├── 选修专题/                 # Web、RAG、多 Agent
├── 课程治理/                 # 规则与迁移映射
├── 参考资料/
└── 归档/2026-07-深度重构前/  # 56 节旧课与 56 份旧面试题
```

## 历史与限制

旧课程全部只读归档，完整去向见 [旧课迁移映射](课程/课程治理/旧课迁移映射.md)。仓库根部和 `agent-from-scratch/` 根部的旧 Python 脚本不是新主线入口；后者受本机企业 TSD/DLP 驱动影响，Git 读取会被替换成保护容器，因此在安全策略解除前不批量移动或重写，具体见 [Git 与 TSD 环境说明](课程/课程治理/Git与TSD环境说明.md)。当前正式实现只位于 `agent-from-scratch/src/agent_from_scratch/`。

Web 工作台、RAG 和多 Agent 均为有进入条件的选修扩展，不能当作当前已交付能力。
