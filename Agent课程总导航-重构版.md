# Agent 课程总导航 - 重构版

## 说明

这份文档不是新的“课程点评”，而是基于 [Agent课程总审计与重构版.md](./Agent课程总审计与重构版.md) 对当前已经生成的课程内容做出的 **直接重构编排结果**。

目标是把现在已经写出来的内容，从：

- 线性堆叠的课程笔记

重组为：

- 分阶段
- 分目标
- 分工程能力层级

的一套真正适合培养 `Agent 开发工程师` 的学习路线。

从现在开始，后续课程建议全部按照这份导航继续推进。

---

## 新版课程总结构

重构后，课程分为四个阶段：

### 阶段 1：Agent 核心认知

目标：

> 建立正确心智模型，避免成为“会调框架 API，但不理解底层”的使用者。

### 阶段 2：从零实现最小 Agent Framework

目标：

> 做出一个真正可运行、可扩展、结构清晰的单 Agent 系统。

### 阶段 3：工程化能力

目标：

> 从“能跑”升级到“可维护、可调试、可测试、可恢复”。

### 阶段 4：高级能力与源码阅读

目标：

> 从“会实现”升级到“会理解、会扩展、会设计 Agent Framework”。

---

## 阶段 1：Agent 核心认知

### 这一阶段保留的课程

这部分建议保留为“前置理论地基”，但不再继续扩展重复内容。

#### Lesson 1

- [第一课-批改整理.md](./第一课-批改整理.md)
- [第一课-面试题整理.md](./第一课-面试题整理.md)

核心主题：

- Agent 是什么
- Agent 与普通 LLM 的区别
- Agent 与 Workflow 的区别
- Tool 为什么决定能力边界
- Observe 为什么关键

#### Lesson 2

- [第二课-学习整理.md](./第二课-学习整理.md)
- [第二课-面试题整理.md](./第二课-面试题整理.md)

核心主题：

- Tool Calling 本质
- JSON / 结构化调用意图
- LLM 不执行 Tool，程序才执行 Tool
- Tool 的 Name / Description / Parameters / Function

#### Lesson 3

- [第三课-学习整理.md](./第三课-学习整理.md)
- [第三课-面试题整理.md](./第三课-面试题整理.md)

核心主题：

- 最小 Agent 项目结构
- `main.py / agent.py / tools.py / prompts.py / config.py`
- 让 LLM 决策，而不是写死 `if...else`

#### Lesson 4

- [第四课-学习整理.md](./第四课-学习整理.md)
- [第四课-面试题整理.md](./第四课-面试题整理.md)

核心主题：

- 环境准备
- 第一个 Tool 的设计
- Schema 是什么
- 用户世界 / LLM 世界 / Python 世界

#### Lesson 5-8 合并理解

- [第五课-学习整理.md](./第五课-学习整理.md)
- [第六课-学习整理.md](./第六课-学习整理.md)
- [第七课-学习整理.md](./第七课-学习整理.md)
- [第八课-学习整理.md](./第八课-学习整理.md)

这一组建议合并为：

> Agent Runtime 核心认知模块

核心主题：

- Agent 本质是 `while True`
- Responses API 的事件输出
- `response.output` 比 `output_text` 更重要
- Agent 本质是 State Machine
- Runner 是 Loop 的宿主
- Agent 是 Runtime，不只是一个类

---

## 阶段 1 需要压缩的内容

下面这些主题在旧课程里已经反复出现，不建议后续再单独展开成长篇：

- 为什么 Agent 需要 Loop
- 为什么 Agent 和 Runner 要分开
- 为什么要 Responses API
- 为什么需要 LLM Interface
- 为什么 Agent 不是 ChatGPT

后续统一作为“必背结论”引用即可，不再反复大段讲解。

---

## 阶段 2：从零实现最小 Agent Framework

### 这一阶段是当前课程的主线

建议从现在开始，把主要学习精力从“新增概念”转向“推进项目代码 + 课程沉淀同步”。

当前已生成内容如下：

#### Sprint 1 - Lesson 1

- [Sprint1-Lesson1-学习整理.md](./Sprint1-Lesson1-学习整理.md)
- [Sprint1-Lesson1-面试题整理.md](./Sprint1-Lesson1-面试题整理.md)

对应能力：

- 初始化 Agent 架构
- `Agent / Runner / BaseLLM` 的职责边界

#### Sprint 1 - Lesson 2

- [Sprint1-Lesson2-学习整理.md](./Sprint1-Lesson2-学习整理.md)
- [Sprint1-Lesson2-面试题整理.md](./Sprint1-Lesson2-面试题整理.md)

对应能力：

- `BaseLLM`
- `OpenAILLM`
- `Runner -> LLM -> Responses API`

#### Sprint 1 - Lesson 3

- [Sprint1-Lesson3-学习整理.md](./Sprint1-Lesson3-学习整理.md)
- [Sprint1-Lesson3-面试题整理.md](./Sprint1-Lesson3-面试题整理.md)

对应能力：

- 第一个真正的最小 Agent Loop
- Tool Call -> Tool Result -> Final Answer

#### Sprint 1 - Lesson 4

- [Sprint1-Lesson4-学习整理.md](./Sprint1-Lesson4-学习整理.md)
- [Sprint1-Lesson4-面试题整理.md](./Sprint1-Lesson4-面试题整理.md)

对应能力：

- 多 Tool 支持
- 从单 Tool 升级到最小 Registry 思维

#### Sprint 1 - Lesson 5

- [Sprint1-Lesson5-学习整理.md](./Sprint1-Lesson5-学习整理.md)
- [Sprint1-Lesson5-面试题整理.md](./Sprint1-Lesson5-面试题整理.md)

对应能力：

- 正式抽出 `ToolManager`
- Runner 从工具细节里解耦

#### Sprint 1 - Lesson 6

- [Sprint1-Lesson6-学习整理.md](./Sprint1-Lesson6-学习整理.md)
- [Sprint1-Lesson6-面试题整理.md](./Sprint1-Lesson6-面试题整理.md)

对应能力：

- Prompt 与 Message 组织
- Tool Result 回填规则
- 为 Session 铺路

---

## 阶段 2 建议新增的课程

为了让 `Sprint 1` 真正完成“最小 Agent Framework”的闭环，建议继续补下面几节：

### Sprint 1 - Lesson 7

主题：

> Session 初版

目标：

- 把 `messages` 从 Runner 局部变量升级为会话对象
- 为后续多轮对话和 Memory 打基础

### Sprint 1 - Lesson 8

主题：

> 最小测试

目标：

- 测试 ToolManager
- 测试 Runner 的最小 Loop
- 测试 Tool Result 回填

### Sprint 1 - Lesson 9

主题：

> 错误处理初版

目标：

- Tool 执行失败怎么办
- LLM 调用失败怎么办
- 最小异常边界在哪里

### Sprint 1 - Lesson 10

主题：

> Sprint 1 重构课

目标：

- 把 lesson 版实现收敛回主文件
- 减少技术债
- 输出第一个“稳定单 Agent”

---

## 阶段 2 完成标准

这一阶段结束时，项目至少应该具备：

- 单 Agent
- 多 Tool
- LLM 抽象层
- ToolManager
- Prompt / Message 组织
- Session 初版
- 最小测试
- 最小错误处理

如果做不到这些，就不要急着往 MCP / Multi-Agent 推。

---

## 阶段 3：工程化能力

这一阶段是当前课程里还没有真正展开、但对“成为工程师”非常关键的一层。

建议新增如下模块：

### 模块 1：Logging

目标：

- 能看见 Agent 在做什么
- 能区分模型调用、Tool 执行、结果回填

### 模块 2：Tracing

目标：

- 给一次运行加上结构化轨迹
- 为后续调试和分析行为路径做准备

### 模块 3：Retry / Timeout / Cancellation

目标：

- Tool 卡住怎么办
- LLM 失败怎么办
- 长任务如何中断

### 模块 4：配置管理

目标：

- 模型、环境、API Key、provider 配置统一管理

### 模块 5：Token / Context 管理

目标：

- 上下文过长怎么办
- 如何压缩消息
- 如何裁剪历史

### 模块 6：Tool 安全边界

目标：

- 哪些 Tool 可以执行
- 哪些输入必须拦截
- 为什么 Coding Agent 天生有安全风险

### 模块 7：Checkpoint / Resume

目标：

- 长任务中断后如何恢复
- 为什么这会直接影响真实生产可用性

---

## 阶段 4：高级能力与源码阅读

这一阶段不建议太早开始，但必须进总路线。

建议新增如下主线：

### 模块 1：OpenAI Agents SDK 源码拆解

重点：

- `Agent`
- `Runner`
- `function_tool`
- `Session`
- `ModelSettings`

### 模块 2：MCP

重点：

- MCP Client
- MCP Server
- 为什么 MCP 比直接写 Tool 更标准

### 模块 3：RAG

重点：

- Retrieval
- chunking
- context 注入
- Agent 与知识库结合

### 模块 4：Multi-Agent

重点：

- Planner
- Executor
- Reviewer

### 模块 5：Claude Code / OpenHands 架构分析

重点：

- 为什么它们的 Loop 更复杂
- 为什么需要更完整的 Runtime

---

## 已生成课程内容的处理原则

从现在开始，建议按下面规则看待现有内容：

### 1. 前 1 到 8 课

作为：

> 前置理论阶段

保留，但不再继续扩讲同类概念。

### 2. 第 9 到 12 课

作为：

> 从理论切换到项目的过渡阶段

可继续保留，但不再作为后续课程主节奏。

### 3. Sprint 1

从现在开始作为：

> 真正的主课程主线

后续应优先继续写 Sprint，不再回到纯理论章节节奏。

---

## 后续课程生成规范

为了保证课程不再重新滑回“理论偏多”的状态，建议从这一版开始统一执行以下规则：

### 规则 1

每一节必须对应一个明确工程目标。

### 规则 2

每一节必须对应项目中的一个真实模块变化。

### 规则 3

每一节都要有：

- 目标
- 实现
- Code Review
- 官方框架视角
- 作业

### 规则 4

每完成 3 到 4 节，必须有一次“重构课”或“测试课”。

### 规则 5

没有完成单 Agent 的工程闭环前，不进入：

- MCP
- Multi-Agent
- RAG
- Long-running Agent

---

## 你现在应该如何使用这份重构版

从现在开始，建议这样用：

1. 前面课程作为基础认知库保留
2. `Sprint 1` 作为当前真实主线
3. 后续所有新课都按重构版的阶段结构继续生成
4. 每完成一阶段，做一次阶段复盘与代码收敛

也就是说：

> 老课程不删除，但主节奏正式切到重构后的阶段路线。

---

## 当前最合理的下一步

基于这份重构版，当前课程最自然的后续顺序是：

1. `Sprint1-Lesson7：Session 初版`
2. `Sprint1-Lesson8：最小测试`
3. `Sprint1-Lesson9：错误处理初版`
4. `Sprint1-Lesson10：Sprint 1 重构课`

完成这四节之后，你的课程就会真正从“知道怎么做 Agent”升级成“拥有一个稳定的最小 Agent Framework”。

