# 阶段二 - Sprint 主线 - 重构整理

## 阶段目标

这一阶段的目标是：

> 从零做出一个最小但真正可运行的 Agent Framework

这里不是做一个零散 demo，而是做一个能够继续迭代的项目骨架。

---

## 当前已经完成的 Sprint 内容

### Sprint 1 - Lesson 1

主题：

- 初始化 Agent 架构
- `Agent / Runner / BaseLLM`

### Sprint 1 - Lesson 2

主题：

- `BaseLLM`
- `OpenAILLM`
- 第一次打通 Responses API

### Sprint 1 - Lesson 3

主题：

- 最小 Agent Loop

### Sprint 1 - Lesson 4

主题：

- 多 Tool 支持

### Sprint 1 - Lesson 5

主题：

- 抽出 `ToolManager`

### Sprint 1 - Lesson 6

主题：

- Prompt 与 Message 组织

---

## 这一阶段后续必须补的内容

### Sprint 1 - Lesson 7

主题：

- Session 初版

### Sprint 1 - Lesson 8

主题：

- 最小测试

### Sprint 1 - Lesson 9

主题：

- 错误处理初版

### Sprint 1 - Lesson 10

主题：

- Sprint 1 重构与收敛

---

## 阶段完成标准

这一阶段结束时，项目应至少具备：

- 单 Agent
- 多 Tool
- ToolManager
- LLM 抽象层
- Prompt / Message 组织
- Session 初版
- 最小测试
- 最小异常边界

如果这些还没完成，就不建议过早进入 MCP、RAG、Multi-Agent。

