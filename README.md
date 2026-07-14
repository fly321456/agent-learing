# Coding Agent Learning Lab

这是一个面向 Python 开发者的 Agent 学习与项目仓库。学习者从一个单文件离线脚本开始，用 32 节循序渐进的课程理解 Agent、Tool Calling 和 Agent Loop，最终完成可安装、可测试、可评测并支持 MCP 的 Coding Agent。

> 当前进度：模块 1 的 L01–L04 已完成教材级精写；模块 2–8 已完成课程结构和项目增量设计，正文仍是待逐模块精写的课程大纲。以 [课程首页的状态表](课程/README.md#当前编写进度) 为准。

## 从这里开始

1. 打开 [32 节课程首页](课程/README.md)。
2. 从 `agent-from-scratch/course-checkpoints/00-starter/` 创建个人学习副本。
3. 每节课先画运行轨迹，再完成一个代码增量和验证。
4. 每 4 课运行模块检查点，并完成模块项目验收与面试。

## 学习路线

```text
Agent 核心认知
  -> LLM 与 Tool Calling
  -> 从零实现 Agent Loop
  -> Runtime 模块化重构
  -> 安全 Coding Tools
  -> Session、上下文与可靠性
  -> 测试、评测与可观测性
  -> CLI、MCP 与作品化
```

主线共 8 个模块、32 节课，预计 40–48 小时。MCP 是必修；RAG 和多 Agent 各有 4 节完整选修课。Web 工作台不属于当前主线。

## 主项目

[agent-from-scratch](agent-from-scratch/README.md) 同时提供三种代码视角：

- `course-checkpoints/`：starter 和 8 个模块完成态，用于学习和恢复。
- `.learning/current/`：被 Git 忽略的个人逐课练习目录。
- `src/agent_from_scratch/`：最终工程参考答案和正式 Python 包。

## 离线验证

```powershell
cd agent-from-scratch
python -m pip install -e ".[dev,mcp]"
python -m pytest -q
python examples/offline_demo.py
coding-agent-eval
```

真实模型实验需要显式设置 `OPENAI_API_KEY` 和 `OPENAI_MODEL`，不属于默认验收，也不会在离线测试中产生费用。

## 历史与安全

原 56 节课程、56 份面试题和项目里程碑版均无损归档，去向见 [历史课程到新主线映射](课程/课程治理/历史课程到新主线映射.md)。8 个旧根 Python 文件仍受企业 TSD/DLP 驱动影响，禁止用 `git add -A` 误提交保护容器；详见 [Git 与 TSD 环境说明](课程/课程治理/Git与TSD环境说明.md)。
