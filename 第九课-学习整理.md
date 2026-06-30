# 第九课学习整理：启动 Coding Agent 项目

## 本课定位

从这一课开始，课程不再以零散概念为中心，而是正式进入一个长期项目：

> 开发一个自己的 Coding Agent

这意味着后续所有学习都会围绕一个真实工程逐步展开，而不是继续停留在“懂很多理论，但还没真正做项目”的状态。

这一课的核心转变是：

> 从学习 Agent 概念，进入设计 Agent Framework

---

## 为什么现在要切项目模式

前面几节课已经完成了这些基础认知：

- Agent 是什么
- Tool Calling
- Agent Loop
- Responses API
- State Machine

如果继续只讲理论，最容易出现的问题就是：

> 理解越来越多，但始终没有形成真正的工程能力

而优秀的 Agent 工程师，几乎都是在项目里成长起来的。

所以从第九课开始，课程升级为：

- 以项目为主线
- 以架构拆分为重点
- 以框架设计能力为目标

---

## 项目目标：开发一个 Coding Agent

后续课程的核心项目结构目标如下：

```text
coding-agent/
│
├── app.py
├── agent.py
├── runner.py
├── tools/
│   ├── file_tool.py
│   ├── shell_tool.py
│   ├── search_tool.py
│   └── python_tool.py
├── prompts/
├── memory/
├── session/
├── mcp/
└── tests/
```

这个项目最终希望具备的能力是：

```text
用户：
帮我分析这个 SpringBoot 项目

↓

Agent：
读取目录
↓
读取 pom.xml
↓
分析 Controller
↓
分析 Service
↓
总结项目架构
↓
输出 Markdown 报告
```

这已经非常接近现代 Coding Agent 的核心工作模式。

也就是说，这个课程后面不再只是教“怎么调用模型”，而是开始逐步做出一个类似 Claude Code 思路的系统雏形。

---

## 普通 Python 程序为什么不能扩展

很多人的 LLM 程序一开始都是这样：

```python
question = input()

response = client.responses.create(...)

print(response.output_text)
```

这种写法在 Demo 阶段没有问题，但一旦能力增加，就会迅速失控。

因为后面很快会出现越来越多的模块需求：

- Calculator
- Weather
- Git
- Filesystem
- Browser
- Memory
- MCP
- 更多 Tool

如果仍然把所有东西堆在一个入口文件里，最终 `main.py` 很容易变成几千行的混合脚本：

- 模型调用逻辑
- 工具分发逻辑
- 会话管理
- 状态循环
- 配置读取
- Prompt 拼接

全部耦合在一起。

这类程序通常“能跑”，但不具备可维护性，也不具备框架演进能力。

---

## 现代 Agent Framework 的典型架构

这一课给出的核心架构图可以理解为：

```text
                User
                  │
                  ▼
              Runner
                  │
        ┌─────────┴──────────┐
        ▼                    ▼
     Session              Agent
                               │
                 ┌─────────────┼────────────┐
                 ▼             ▼            ▼
             Prompt        Memory        ToolManager
                                              │
                                    ┌─────────┴────────┐
                                    ▼                  ▼
                                 Tool1             Tool2
```

这张图的重点不是“类很多”，而是：

> 把配置、运行、状态、记忆、工具执行分到不同层

这就是现代 Agent Framework 的基本设计方向。

---

## 今天只实现一个类：`Agent`

这一课有意控制节奏，不会一次写很多文件。

今天只讨论并设计一个类：

> `Agent`

这是一个非常重要的教学策略，因为很多初学者最大的问题不是“不会写”，而是“一上来什么都写进一个类里”。

这一课要建立的第一个软件设计习惯是：

> 先控制职责，再开始实现

---

## Agent 不应该负责什么

很多新人很容易写出这样的类：

```python
class Agent:

    def run()
    def call_tool()
    def remember()
    def save()
    def retry()
    def loop()
```

看起来功能很多，但这通常是错误的方向。

问题不在于“能不能写”，而在于：

> 这个类承担了太多职责

如果一个类同时负责：

- 配置
- 运行
- 重试
- 工具执行
- 记忆持久化
- 生命周期管理

那么这个类很快就会变成不可维护的“上帝对象”。

---

## Agent 应该负责什么

这一课给出了一个非常清晰的边界：

Agent 只负责回答这些问题：

```text
我是一个什么样的智能体？
我有哪些 Tool？
我使用哪个模型？
我的 Prompt 是什么？
```

也就是说，Agent 本质上保存的是：

- 名字
- 指令或 Prompt
- 模型
- Tools

它不负责：

- 运行 Loop
- Retry
- Session 生命周期
- Memory 管理流程

这些以后都交给其他模块。

这是非常典型的职责控制思想。

---

## 为什么要把 Agent 和 Runner 分开

课程这里明确对齐了 OpenAI Agents SDK 的一个关键设计：

为什么同时存在：

- `Agent`
- `Runner`

很多新人会直觉觉得：

> 合并成一个类不好吗？

但从软件设计角度看，分开更合理。

原因在于：

### Agent

负责：

- 定义能力
- 保存配置
- 描述身份与边界

### Runner

负责：

- 执行整个 Loop
- 驱动运行时状态
- 协调工具调用与模型交互

这样设计后，一个 Runner 理论上可以运行多个不同 Agent：

- Agent A
- Agent B
- Agent C

甚至进一步支持 Multi-Agent 协作。

这背后体现的是经典原则：

> 单一职责原则

也就是：

- Agent 负责“我是谁”
- Runner 负责“我怎么运行”

---

## 我们自己的第一版 Agent 设计

第一版 Agent 的初始化可以非常简单：

```python
class Agent:

    def __init__(
        self,
        name,
        instructions,
        model,
        tools
    ):
        ...
```

只保留四类核心配置：

- `name`
- `instructions`
- `model`
- `tools`

这个设计背后有一个非常重要的认识：

> Agent 更像 Configuration，而不是 Runtime

例如：

### Name

```text
Code Reviewer
```

### Instructions

```text
你是一名高级 Java 工程师，请帮助分析项目架构……
```

### Tools

```text
Read File
Shell
Git
```

### Model

```text
gpt-5
```

这些信息组合在一起，构成了一个 Agent 的静态身份定义。

但请注意：

> 这时它还没有开始工作

真正让它工作起来的，是 Runner。

---

## 真正运行的是 Runner

未来运行方式会更接近这样：

```python
Runner.run(
    agent,
    "帮我分析项目"
)
```

此时 Runner 才会真正进入：

```text
while True
↓
LLM
↓
Tool
↓
LLM
↓
……
```

所以可以总结成一句非常关键的话：

> Agent 拥有配置，Runner 拥有生命周期

这也是现代 Agent Framework 的底层分层思想之一。

---

## 现代 Agent Framework 的共同设计模式

这一课把很多不同框架抽象成了同一个底层模型：

```text
Configuration
+
Runtime
```

或者更具体一点：

```text
Agent
+
Runner
```

无论是：

- OpenAI
- LangGraph
- AutoGen
- CrewAI
- OpenHands

虽然 API 长得不一样，但底层都在解决相似问题：

- 怎样描述一个 Agent
- 怎样执行一个 Agent

因此，理解 `Agent + Runner` 这个分层，比记忆某个框架 API 更重要。

---

## 本课最重要的一句话

这节课最值得长期记住的设计思想是：

> Agent 负责“我是谁”，Runner 负责“我怎么运行”

这句话本质上是在训练一种框架设计能力：

- 不把配置和运行耦合
- 不把身份定义和生命周期管理混在一起
- 不把能力描述和执行控制写进同一个对象

这几乎是后面所有 Agent 架构设计的基础。

---

## 课后设计题

如果现在让你设计一个“GitHub 项目分析 Agent”，不要先想代码，而是先拆模块：

### Agent 应该保存哪些配置？

例如：

```text
Agent
├── ?
├── ?
├── ?
└── ?
```

### Runner 应该负责哪些事情？

例如：

```text
Runner
├── ?
├── ?
├── ?
└── ?
```

这个题目真正训练的是“架构分层能力”，也是很多 AI Agent 岗位面试非常典型的题型。

---

## 下一步

从下一课开始，课程将进入“迷你版 OpenAI Agents SDK”实现阶段，逐步完成：

- `Agent`
- `Runner`
- `Tool`
- `Session`
- `Memory`
- `Result`
- `Tracing`

最终再升级到支持：

- MCP
- 多 Agent
- RAG
- 长生命周期任务
- Checkpoint 自动恢复

也就是说，从这一课开始，课程已经真正从“学习 Agent”转向“设计 Agent Framework”。

