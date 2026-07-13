# Coding Agent 项目课程

本目录是仓库唯一课程入口。主线不再按“下一课”无限扩展，而是以 `agent-from-scratch` 中可运行、可测试、可答辩的项目成果为完成标准。

## 学习方式

1. 阅读当前里程碑的 `课程.md`。
2. 在 `agent-from-scratch/` 中完成或复核对应代码。
3. 执行文档中的自动验证命令。
4. 使用 `验收与面试.md` 做代码讲解、故障分析和设计答辩。
5. 产物未通过验收前，不进入下一个里程碑。

## 八个主线里程碑

| 里程碑 | 课程 | 验收与面试 | 项目结果 |
| --- | --- | --- | --- |
| M01 | [运行基线](主线-Coding-Agent/M01-运行基线/课程.md) | [验收](主线-Coding-Agent/M01-运行基线/验收与面试.md) | 标准 Python 包、LLM 抽象、离线测试 |
| M02 | [Agent Loop](主线-Coding-Agent/M02-Agent-Loop/课程.md) | [验收](主线-Coding-Agent/M02-Agent-Loop/验收与面试.md) | 文本、单/多 Tool 与受控终止 |
| M03 | [安全 Coding Tools](主线-Coding-Agent/M03-安全-Coding-Tools/课程.md) | [验收](主线-Coding-Agent/M03-安全-Coding-Tools/验收与面试.md) | 工作区工具、审批、越界与超时保护 |
| M04 | [响应协议与事件流](主线-Coding-Agent/M04-响应协议与事件流/课程.md) | [验收](主线-Coding-Agent/M04-响应协议与事件流/验收与面试.md) | LLMResponse、ToolResult、RunResult、Event |
| M05 | [Session 与上下文](主线-Coding-Agent/M05-Session与上下文/课程.md) | [验收](主线-Coding-Agent/M05-Session与上下文/验收与面试.md) | 会话、预算、检查点与恢复 |
| M06 | [可靠性与可观测性](主线-Coding-Agent/M06-可靠性与可观测性/课程.md) | [验收](主线-Coding-Agent/M06-可靠性与可观测性/验收与面试.md) | Retry、Timeout、错误分类与 Trace |
| M07 | [测试与评测](主线-Coding-Agent/M07-测试与评测/课程.md) | [验收](主线-Coding-Agent/M07-测试与评测/验收与面试.md) | 分层测试、20 题任务集与回归指标 |
| M08 | [扩展与作品化](主线-Coding-Agent/M08-扩展与作品化/课程.md) | [验收](主线-Coding-Agent/M08-扩展与作品化/验收与面试.md) | CLI、最小 MCP、发布说明与扩展审计 |

## 选修专题

- [响应协议与 Web 工作台契约](选修专题/响应协议与Web工作台契约.md)
- [RAG 与外部知识实验](选修专题/RAG与外部知识实验.md)
- [多 Agent 可拆分性审计](选修专题/多Agent可拆分性审计.md)

选修内容必须先满足进入条件。Web 不属于核心依赖；RAG 和多 Agent 不能只因技术热门而引入。

## 治理与历史

- [课程架构与维护规则](课程治理/课程架构与维护规则.md)
- [旧课迁移映射](课程治理/旧课迁移映射.md)
- [Git 与 TSD 环境说明](课程治理/Git与TSD环境说明.md)
- [深度重构前归档](归档/2026-07-深度重构前/)
- [历史参考资料](参考资料/)

归档只读，不再维护第二套课程主线。发现历史内容与当前 API 冲突时，以新主线、项目测试和课程中标注的官方核验日期为准。

## 一键验证

```powershell
cd agent-from-scratch
python -m pip install -e ".[dev,mcp]"
python -m pytest -q
python examples/offline_demo.py
coding-agent-eval
```
