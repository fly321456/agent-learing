# Sprint 1 - Lesson 1 学习整理

## 本节定位

从这一节开始，课程正式从“概念学习”切换到“项目开发”。

这一节的目标不是把 Agent 一次写完，而是先搭出最小工程骨架，并明确最核心的职责拆分：

- `Agent` 只负责配置
- `Runner` 只负责运行
- `LLM` 先定义抽象接口

这一步非常关键，因为它决定了后面整个项目是不是会演化成一个清晰的 Agent Framework，而不是一个堆满逻辑的大脚本。

---

## 本节目标

真正实现并理解下面这个最小运行结构：

```text
User
  │
  ▼
Runner
  │
  ▼
LLM
  │
  ▼
是否调用 Tool？
  │
 ├── 否 → 返回答案
 │
 └── 是
      │
      ▼
执行 Tool
      │
      ▼
Tool Result
      │
      ▼
LLM
      │
      ▼
最终答案
```

这一套结构几乎就是大多数 Agent Framework 的核心。

---

## 本节最重要的设计点

很多初学者会本能地写出：

```python
class Agent:
    def run(self):
        ...
```

这节课明确指出这不是一个好的第一版设计。

原因是：

> Agent 是配置，不是执行器。

所以第一版必须拆成两个类：

- `Agent`
- `Runner`

这是后续理解 OpenAI Agents SDK、LangGraph、OpenHands 等框架的关键前提。

---

## Agent 负责什么

第一版 `Agent` 只保存最核心的静态配置：

```python
class Agent:
    def __init__(self, model, instructions, tools):
        self.model = model
        self.instructions = instructions
        self.tools = tools
```

这里有几个重要结论：

- `Agent` 不包含 `run()`
- `Agent` 不处理 Loop
- `Agent` 不负责 Tool 执行
- `Agent` 不直接管理 Memory / Session / Retry

也就是说：

> Agent 回答的是“我是谁”

它更像一个能力配置对象，而不是一个完整运行时。

---

## Runner 负责什么

真正运行的是 `Runner`：

```python
class Runner:
    def run(self, agent, user_input):
        ...
```

这里为什么是：

```python
run(agent, user_input)
```

而不是：

```python
self.agent
```

因为这意味着一个 `Runner` 可以运行多个不同 Agent，例如：

- Code Agent
- Review Agent
- Search Agent

这会让系统更灵活，也更符合框架设计思路。

所以：

> Agent 负责定义能力，Runner 负责驱动生命周期。

---

## 本节背后的软件工程思想

这一节实际上在训练两个非常重要的工程原则。

### 1. 高内聚、低耦合

- `Agent` 只管 Agent 的配置
- `Runner` 只管运行过程

不要把所有逻辑都塞进一个类里。

### 2. 单一职责

一个类只做一件事：

- `Agent`：定义智能体
- `Runner`：执行流程
- `BaseLLM`：定义模型接口

这也是为什么优秀 Agent 框架源码通常可读性更高。

---

## LLM 抽象为什么现在就要加

这一节虽然还没有真正接 OpenAI，但已经先把 `llm.py` 放进了项目结构中。

原因是：

很多初学者会在项目里到处直接写：

```python
client.responses.create(...)
```

这样一旦底层模型发生变化，例如：

- GPT
- Claude
- Gemini
- Qwen

整个项目都要跟着改。

所以应该先定义统一接口，例如：

```python
class BaseLLM:
    def generate(self, messages, tools=None):
        raise NotImplementedError
```

这样上层系统只依赖：

```python
generate()
```

而不依赖某个具体供应商 SDK。

这本质上就是：

> 依赖倒置

---

## 本节项目结构

本节完成后的最小项目骨架如下：

```text
agent-from-scratch/
│
├── app.py
├── config.py
├── llm.py
├── agent.py
├── runner.py
├── tools.py
├── schemas.py
├── prompts.py
└── requirements.txt
```

这套结构的意义在于：

- `app.py`：程序入口
- `agent.py`：Agent 定义
- `runner.py`：运行器
- `llm.py`：模型抽象接口
- `tools.py`：工具实现
- `schemas.py`：工具 Schema
- `prompts.py`：Prompt 资源
- `config.py`：配置

虽然现在很多文件还是占位，但骨架已经正确了。

---

## 本节代码成果

### `agent.py`

实现了最小 `Agent` 配置类。

### `runner.py`

实现了第一版 `Runner.run()`，暂时只做最简单的输入和状态输出。

### `llm.py`

实现了 `BaseLLM` 抽象接口，下一节将继续扩展为 `OpenAILLM`。

### `app.py`

完成了最小启动流程：

```python
agent = Agent(...)
runner = Runner()
runner.run(agent, ...)
```

这意味着项目已经从“纯笔记”正式进入“可运行骨架”阶段。

---

## 本节 Git Commit

建议的提交信息：

```text
Initialize Agent Architecture
```

这个 Commit 的意义不是功能完整，而是：

> 确立了后续整个 Agent 项目的基础架构边界。

---

## 本节最值得记住的三句话

### 1.

> Agent 是配置，不是执行器。

### 2.

> Runner 才是真正驱动 Agent Loop 的地方。

### 3.

> LLM 要先抽象，再接具体实现。

---

## 下一步

下一节将进入整个项目第一次真正调用模型的阶段：

- `BaseLLM`
- `OpenAILLM`
- `Responses API`

到那时，项目会第一次形成：

```text
Agent
  ↓
Runner
  ↓
BaseLLM
  ↓
OpenAILLM
  ↓
Responses API
```

这会是整个 Agent Framework 最关键的一层抽象落地。

