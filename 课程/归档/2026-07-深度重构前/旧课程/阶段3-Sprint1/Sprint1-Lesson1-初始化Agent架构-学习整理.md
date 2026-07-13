# Sprint1 - Lesson1 学习整理：初始化 Agent 架构

## 本节定位

从这一节开始，课程正式从“阶段 2 的项目过渡”进入“阶段 3 的 Sprint1 实战实现”。

如果说阶段 2 解决的是：

- 为什么要做自己的 Coding Agent
- 为什么要抽象 `LLM Interface`
- 为什么要先理解 OpenAI Agents SDK
- 为什么要先写出 100 行以内的最小 Agent
- 为什么输出不能只停留在纯文本
- 为什么需要 `LLMResponse` 这样的统一响应协议

那么 Sprint1-Lesson1 要解决的就不再是“理解为什么”，而是：

> 在 `agent-from-scratch/` 里，先把第一版可演进的工程骨架搭出来

也就是说，这一节的目标不是一次写完 Agent，而是：

> 先把整个项目最关键的职责边界立住

---

## 为什么 Sprint1 不能直接从“写功能”开始

很多初学者进入项目实战时，很容易一上来就想：

- 先把 `run()` 写出来
- 先把 OpenAI 调起来
- 先把 Tool Calling 跑通

这样做短期看很快，但中期就很容易出问题。

因为一旦一开始没有把边界立清楚，后面最常见的结果就是：

- `Agent` 又存配置又跑逻辑
- `Runner` 不存在，或者只是一个空壳
- `llm.py` 只是 SDK 调用片段
- 工具、Prompt、Schema、配置混在一起
- 后面再想加 Session、Tracing、`LLMResponse` 会越来越别扭

所以 Sprint1 的第一课不应该追求“先跑起来”，而应该先解决一个更底层的问题：

> 这个项目的第一版结构，是否具备继续演进成 Agent Framework 的可能性

---

## 这节课和阶段 2 的衔接关系

要真正看懂这一节，最好把它放在前面几课的延长线上理解。

### 第九课告诉我们

> 从现在开始不是继续堆概念，而是开始围绕真实项目推进

### 第十课告诉我们

> 模型调用应该被隔离到 `LLM Interface` 后面

### 第十一课告诉我们

> 官方框架的价值在于分层和职责边界，而不是魔法 API

### 第十二课告诉我们

> 一个最小 Agent 的核心闭环其实就是 `LLM -> Tool -> LLM -> Finish`

### 第十三课告诉我们

> 输出不能长期停留在纯文本，未来一定会走向结构化协议

### 第十四课告诉我们

> 结构化协议最终会落成 `LLMResponse / ToolCall / Event / Block`

那么 Sprint1-Lesson1 在这个链路中的任务就非常明确：

> 先给这些抽象预留正确的位置，让后面的实现不会把它们挤碎

---

## 本节真正要完成的不是功能，而是骨架

这节课结束时，最重要的成果不是“功能有多完整”，而是下面这个问题有没有回答清楚：

```text
这个项目里，谁负责定义 Agent？
谁负责运行 Agent？
谁负责模型调用边界？
谁负责 Tool？
谁负责 Schema？
谁负责 Prompt？
谁负责配置？
```

只要这些职责还混在一起，后面功能写得越多，返工成本就越高。

所以这一节的目标，实际上是把下面这套最小工程骨架立起来：

```text
agent-from-scratch/
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

这不是为了“看起来像框架”，而是为了保证后续每一层都能继续长。

---

## 这一节最关键的设计点：先拆边界，再写实现

很多同学写第一版 Agent 时，最常见的冲动是：

```python
class Agent:
    def run(self):
        ...
```

这节课最重要的作用，就是先把这种写法纠正掉。

原因不是它“完全不能跑”，而是它从第一天就埋下了混乱边界。

因为一旦 `Agent.run()` 同时承担：

- 接收用户输入
- 组装 messages
- 调模型
- 判断 Tool Call
- 执行 Tool
- 返回结果

那它就不再是“Agent 定义”，而是变成了一个不断膨胀的 God Object。

所以第一版必须先拆成两个角色：

- `Agent`
- `Runner`

这一步非常关键，因为它决定了后面你看到 OpenAI Agents SDK、OpenHands、LangGraph 时，能不能一下子看懂它们为什么会这么分层。

---

## `Agent` 在第一版里到底负责什么

第一版 `Agent` 应该只保存最核心的静态配置。

例如：

```python
class Agent:
    def __init__(self, llm, instructions, tools):
        self.llm = llm
        self.instructions = instructions
        self.tools = tools
```

这里最重要的不是字段有几个，而是职责非常收敛。

第一版 `Agent` 的核心职责应该是：

- 保存使用哪个 `llm`
- 保存系统指令或 Prompt
- 保存当前可用 Tools

也就是说，`Agent` 回答的是：

> 我是谁，我用什么模型能力，我有什么工具，我遵循什么指令

所以它不应该负责：

- `run()`
- Loop
- Tool 执行
- Retry
- Session
- Memory
- Logging
- Tracing

这不是因为这些能力不重要，而是因为它们现在不应该挤进 `Agent` 里。

---

## `Runner` 在第一版里到底负责什么

真正运行 Agent 的，应该是 `Runner`。

例如：

```python
class Runner:
    def run(self, agent, user_input):
        ...
```

这里一个很重要的设计信号是：

```python
run(agent, user_input)
```

而不是：

```python
self.agent.run(...)
```

这意味着 `Runner` 理论上可以运行多个不同的 Agent：

- Code Agent
- Review Agent
- Search Agent

所以 `Runner` 回答的问题是：

> 一个 Agent 应该怎样被驱动起来

第一版 `Runner` 暂时不需要完整实现所有循环细节，但至少要承担：

- 接收用户输入
- 驱动一次调用链入口
- 串起 Agent 与 LLM
- 为后续 Loop 留位置

后面真正的：

- Tool 判定
- 多轮迭代
- 事件流输出
- `LLMResponse` 汇聚

都应该长在 `Runner` 这一侧，而不是回流进 `Agent`。

---

## 为什么 `llm.py` 现在就必须出现

这节课虽然还没有完全进入模型实现细节，但 `llm.py` 必须从第一版目录里出现。

原因非常简单：

如果这层不先立住，后面最容易退化成：

```python
client.responses.create(...)
```

到处散落在 Runner 或 Agent 里。

一旦这样写，后面这些能力都会变难：

- 切换模型供应商
- 测试和 Mock
- 输出协议统一
- `LLMResponse` 落地
- 多模型扩展

所以第一版 `llm.py` 的意义，不是功能完整，而是先把抽象位置占住。

例如：

```python
class BaseLLM:
    def generate(self, messages, tools=None):
        raise NotImplementedError
```

现在先不要求它完整，只要求它存在，并且让上层开始依赖：

> `generate()` 这种统一能力

而不是依赖某家 SDK。

---

## 为什么这一节还不急着把 `LLMResponse` 写进去

你前面已经补了第十三、十四课，所以这里一个很自然的问题就是：

> 既然都已经讲到 `LLMResponse` 了，为什么 Sprint1-Lesson1 不直接把它实现掉？

答案是：这节课的任务还没到那一步。

这一节最重要的是先把骨架摆对。

因为如果现在连：

- `Agent`
- `Runner`
- `BaseLLM`
- Tool
- Schema

这些位置都还没立稳，就直接把 `LLMResponse` 写进来，往往只会让结构更乱。

更合理的顺序应该是：

### 这一节先完成

- 目录结构
- 职责边界
- 类与模块的基本位置

### 后续再逐步补齐

- 真实的 `OpenAILLM`
- 真正的 Agent Loop
- Tool Calling 闭环
- `LLMResponse`
- `Event`
- `Block`

这说明：

> 第十四课提供的是设计方向，而不是要求 Sprint1 第一课立刻把所有协议都实现完

---

## 本节项目结构的意义

这节课完成后的最小项目结构如下：

```text
agent-from-scratch/
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

每个文件的意义应该非常清楚：

- `app.py`：程序入口
- `config.py`：配置管理
- `llm.py`：模型能力边界
- `agent.py`：Agent 定义
- `runner.py`：运行时驱动
- `tools.py`：工具实现
- `schemas.py`：给 LLM 看的 Tool Schema
- `prompts.py`：Prompt 资源

这一节的关键不是每个文件都写很多代码，而是：

> 以后这些职责不再需要临时找地方安放

这就是骨架的价值。

---

## 这一节完成后，系统应该处于什么状态

这一节结束后，项目不一定“功能完整”，但应该已经具备了三个非常重要的特征。

### 1. 结构是清楚的

你已经知道：

- 配置放哪
- Prompt 放哪
- LLM 抽象放哪
- Tool 放哪
- Runner 放哪

### 2. 后续扩展有位置

你以后要加：

- `OpenAILLM`
- Loop
- ToolManager
- Session
- `LLMResponse`

都已经知道该往哪一层长。

### 3. 不会轻易退化成大脚本

这点很关键。

真正糟糕的项目，往往不是一开始就错得很离谱，而是：

> 第一版没有立边界，后面所有新增功能都只能继续往一个文件里塞

这一节的意义，就是从第一天开始避免这种退化。

---

## 本节最值得记住的三句话

### 1.

> Agent 是配置，不是执行器

### 2.

> Runner 才是真正驱动 Agent 生命周期的地方

### 3.

> LLM 要先抽象，再接具体实现

---

## 本节 Git Commit

建议提交信息：

```text
Initialize Agent Architecture
```

这个 Commit 的意义不是功能完整，而是：

> 正式确立了整个 `agent-from-scratch` 项目的基础架构边界

---

## 下一步

下一节最自然的推进方向，是继续把这套骨架接上真实的模型调用链。

也就是说，后面会开始进入：

- `BaseLLM`
- `OpenAILLM`
- `Responses API`

等真正“让骨架开始工作”的阶段。

到那时，项目会第一次形成：

```text
Agent
-> Runner
-> BaseLLM
-> OpenAILLM
-> Responses API
```

也就是说，这一节不是在做功能高潮，而是在做：

> 整个 Sprint1 最关键的起跑姿势
