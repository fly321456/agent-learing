# 阶段一 - Agent 核心认知 - 重构整理

## 阶段目标

这一阶段的目标不是让学习者“会调框架”，而是建立后续全部工程训练的正确心智模型。

如果这一阶段没打牢，后面学习 MCP、RAG、Multi-Agent 时，会非常容易陷入：

> 会说术语，但不知道系统到底在怎么运行。

---

## 建议保留的核心结论

### 1. Agent 不是普通聊天模型

普通 LLM 更接近：

```text
Input -> Inference -> Output
```

Agent 更接近：

```text
LLM -> Tool -> LLM -> Tool -> ... -> Finish
```

### 2. Agent = LLM + Tool + Loop

这是整个课程的第一性原理。

### 3. Tool Calling 的本质是结构化调用意图

LLM 不执行 Python，它只输出：

- 调哪个 Tool
- 传什么参数

真正执行的是程序。

### 4. Responses API 更适合 Agent

因为 Agent 消费的是：

- message
- function_call
- reasoning
- event

而不是只有一段文本。

### 5. Agent Loop 本质是状态机

最小状态流转可以理解为：

```text
CALL_MODEL
-> RECEIVE_RESPONSE
-> TOOL_CALL?
-> EXECUTE_TOOL
-> CALL_MODEL
-> ...
-> FINISH
```

### 6. Agent 是配置，Runner 是运行时

这是一条后续会反复用到的工程边界。

### 7. LLM Interface 是必要抽象

否则项目很快会和某个供应商 SDK 强耦合。

---

## 这一阶段的课程来源

这部分内容主要来自：

- 第一课
- 第二课
- 第三课
- 第四课
- 第五课
- 第六课
- 第七课
- 第八课

以及第九到第十二课里部分与工程切换相关的理论。

---

## 这一阶段的重构原则

### 保留

保留真正构成心智模型的内容。

### 压缩

压缩重复度高的段落，例如：

- 为什么要 Loop
- 为什么 Agent 和 Runner 要分开
- 为什么要 Responses API

### 不再扩讲

从现在开始，这些基础结论不再单独扩讲成长课，而是作为后续 Sprint 的默认前提。

---

## 阶段完成标准

如果学习者能清楚解释下面 6 个问题，就可以认为第一阶段达标：

1. 为什么 ChatGPT 不等于完整 Agent？
2. Tool Calling 本质是什么？
3. 为什么 LLM 不执行 Tool？
4. 为什么 Agent Loop 天生需要循环？
5. 为什么 `Runner` 比 `Agent` 更接近运行时？
6. 为什么 Agent 项目里需要 LLM 抽象层？

只要这 6 个问题能讲清楚，后面就应该尽快进入工程实现，而不是继续反复上理论课。

