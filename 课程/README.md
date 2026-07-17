# Coding Agent 深入浅出课程

这是一条从零理解 Agent、亲手实现 Agent Loop，再逐步成长为工程化 Coding Agent 的连续学习路线。默认学习者已经掌握 Python 基础，但没有 Agent 开发经验。

## 学习原则

1. 先理解问题和运行轨迹，再写代码。
2. 每课只增加一个主要概念和一个可验证增量。
3. 每节 60–90 分钟，讲解约 40%，实践约 60%。
4. 必修实验全部可离线完成，真实 Responses API 是选做实验。
5. 不直接照抄最终 `src/`；从上一模块检查点复制到 `.learning/current/` 后跟课修改。

## 当前编写进度

- **主线与选修均为教材候选版。** 32 节主线和 8 节选修已有正文、离线步骤、答案与专项测试，正式 Runtime 的安全、协议、恢复、评测和可观测性契约已完成本轮校准。
- **“文件齐全”不等于“教学稳定版”。** 发布稳定版前仍须逐模块完成讲师语义复核、至少一次试讲反馈、命令复跑和跨模型对抗审查；未留下复核证据时不得写“全部完成”。
- 状态证据见 [课程能力到最终实现矩阵](课程治理/课程能力到最终实现矩阵.md)。后续禁止仅凭字数或文件数量批量更新完成状态。

## 32 节主线

| 模块 | 课程范围 | 编写状态 | 模块导学 | 项目结果 |
| --- | --- | --- | --- | --- |
| 01 Agent 核心认知 | L01–L04 | **候选版，待试讲复核** | [开始学习](主线-Coding-Agent/模块01-Agent核心认知/模块导学.md) | 离线演示 Think–Act–Observe |
| 02 LLM 与 Tool Calling | L05–L08 | **候选版，技术契约已校准** | [开始学习](主线-Coding-Agent/模块02-LLM与Tool Calling/模块导学.md) | 完成一次单 Tool 固定往返 |
| 03 从零实现 Agent Loop | L09–L12 | **候选版，待试讲复核** | [开始学习](主线-Coding-Agent/模块03-从零实现Agent Loop/模块导学.md) | 得到单文件最小 Agent |
| 04 Runtime 模块化重构 | L13–L16 | **候选版，技术契约已校准** | [开始学习](主线-Coding-Agent/模块04-Runtime模块化重构/模块导学.md) | 重构为标准 Runtime 包 |
| 05 安全 Coding Tools | L17–L20 | **候选版，安全边界已校准** | [开始学习](主线-Coding-Agent/模块05-安全Coding Tools/模块导学.md) | 安全分析、修改和验证代码 |
| 06 Session、上下文与可靠性 | L21–L24 | **候选版，恢复契约已校准** | [开始学习](主线-Coding-Agent/模块06-Session上下文与可靠性/模块导学.md) | 会话、恢复和分级错误处理 |
| 07 测试、评测与可观测性 | L25–L28 | **候选版，评测口径已校准** | [开始学习](主线-Coding-Agent/模块07-测试评测与可观测性/模块导学.md) | 离线测试、20 题评测与 Trace |
| 08 CLI、MCP 与作品化 | L29–L32 | **候选版，分发契约已校准** | [开始学习](主线-Coding-Agent/模块08-CLI-MCP与作品化/模块导学.md) | 可安装、可演示、可答辩的 Coding Agent |

## 如何使用代码检查点

```powershell
cd agent-from-scratch
New-Item -ItemType Directory -Path .learning -Force
Copy-Item -Recurse -Force course-checkpoints/00-starter .learning/current
cd .learning/current
python demo.py
```

模块完成后运行对应的 `course-checkpoints/01-...` 至 `08-...`，比较行为和代码边界。检查点是教学参考，不是正式包 API；最终答案仍位于 `src/agent_from_scratch/`。

## 完整选修模块

- [RAG 与外部知识](选修模块/RAG/模块导学.md)：**教材候选版**，4 课，从无 RAG 基线到检索评测。
- [多 Agent 工程](选修模块/Multi-Agent/模块导学.md)：**教材候选版**，4 课，从可拆分性审计到含独立真值的 Reviewer 对照实验。

完成 32 节主线和单 Agent 基线后再进入选修。

## 治理与历史

- [课程架构与维护规则](课程治理/课程架构与维护规则.md)
- [历史课程到新主线映射](课程治理/历史课程到新主线映射.md)
- [Git 与 TSD 环境说明](课程治理/Git与TSD环境说明.md)
- [课程能力到最终实现矩阵](课程治理/课程能力到最终实现矩阵.md)
- [项目里程碑版归档](归档/2026-07-项目里程碑版/)
- [更早的 56 节课程归档](归档/2026-07-深度重构前/)

## 最终验证

```powershell
cd agent-from-scratch
python -m pip install -e ".[dev,mcp]"
python -m pytest -q
python examples/offline_demo.py
coding-agent-eval
```
