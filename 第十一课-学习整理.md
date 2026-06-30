# 第十一课学习整理：不要先学 LangChain，先学 OpenAI Agents SDK

## 本课定位

从这一课开始，课程正式进入一个更接近真实工程团队培养方式的新阶段：

> 不只是写一个 Agent，而是开始理解 OpenAI Agents SDK 为什么这样设计

这一课的核心不是某个具体 API，而是：

> 建立“官方框架抽象层次”的理解顺序

也就是先掌握底层，再理解官方封装，而不是一上来就使用高层框架黑盒。

---

## 为什么不建议一开始先学 LangChain

很多初学者常见学习路线是：

```text
Python
↓
LangChain
↓
Agent
```

课程明确指出，这条路线并不理想。

原因不是 LangChain 不好，而是：

> 它帮你封装了太多东西

比如：

```python
agent.invoke(...)
```

虽然能快速跑通，但你很可能不知道内部到底发生了什么：

- Tool Schema 是怎么生成的
- Tool Call 是怎么解析的
- Loop 是谁在跑
- Session 是怎么维持的
- 为什么模型能“自动”选 Tool

因此它更适合在底层已经理解之后再去使用。

---

## 更推荐的现代学习路径

课程推荐的路线是：

```text
Python
↓
OpenAI SDK
↓
Responses API
↓
OpenAI Agents SDK
↓
MCP
```

这条路线的好处是每一层职责都更清楚：

- `Python`：语言与工程基础
- `OpenAI SDK`：直接接模型
- `Responses API`：理解现代 Agent 的事件输出结构
- `OpenAI Agents SDK`：理解官方运行时抽象
- `MCP`：理解标准化工具与上下文协议

这会让你后面再看任何其他框架时，都更容易一眼拆穿它的本质。

---

## 本课先做什么：安装官方 SDK

这一课先不写业务代码，而是先进入官方框架视角。

推荐安装：

```bash
pip install openai-agents
```

安装后，可以先关注几个核心对象：

```python
Agent
Runner
function_tool
ModelSettings
```

这里课程特别提醒：

> 不要急着背 API 名字

比 API 更重要的是：

> 为什么官方要把框架拆成这些对象

---

## OpenAI 为什么要设计 `Agent`

很多人第一次看到：

```python
Agent(...)
```

会直觉地把它理解成“一个会自动工作的机器人”。

但课程明确纠正了这个误解：

> Agent 更像 Configuration（配置）

可以把它理解成：

```text
Agent
├── Prompt
├── Model
├── Tools
└── Settings
```

也就是说，Agent 本身主要保存的是：

- Prompt 或 Instructions
- 使用哪个模型
- 可调用哪些 Tools
- 一些模型设置或行为设置

因此：

> Agent 只是能力定义，不是运行过程本身

这和前面课程里反复强调的“Agent 更像配置层”是完全一致的。

---

## 为什么还需要 `Runner`

既然 Agent 只是配置，那么谁来负责真正运行？

答案就是：

```text
Runner
```

课程把职责区分得非常清楚：

- `Agent` 负责：我是谁？
- `Runner` 负责：我怎么运行？

例如：

```python
agent = Agent(...)
```

这一步只是创建了一个能力配置对象。

真正让它工作的是：

```python
Runner.run(agent, "你好")
```

这里应该立刻联想到我们前面一直讲的：

```python
while True:
    ...
```

因为：

> Runner 内部本质上就是 Agent Loop

它负责做的事情包括：

- 接收输入
- 调模型
- 判断是否有 Tool Call
- 执行 Tool
- 把结果送回模型
- 直到任务完成

所以从框架设计角度看：

> `Runner` 是 Runtime，`Agent` 是 Configuration

---

## 为什么 Tool 不能只是普通函数

例如：

```python
def weather(city):
    ...
```

从 Python 的角度看，这当然是可调用的。

但问题在于：

> LLM 并不认识普通 Python 函数

它需要的是一个模型可理解的工具描述，也就是 Tool Schema。

因此官方 SDK 会提供类似：

```python
@function_tool
```

它的意义不是“让 Python 能调用函数”，因为 Python 本来就能调。

它真正的作用是：

> 自动从函数生成 Tool Schema，并把这个函数暴露给 LLM

这里又回到了前面课程反复讲过的 Tool 三要素：

- Name
- Description
- Parameters

官方 SDK 通过装饰器或等价机制，帮助你自动完成这层桥接。

---

## 官方架构可以怎样理解

课程把官方架构简化为：

```text
                 Runner
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
     Agent                  Session
        │
 ┌──────┼──────┐
 ▼      ▼      ▼
Model Prompt Tools
```

未来还会继续增加更多运行时能力，例如：

- Memory
- Tracing
- MCP
- Guardrails

这张图的意义在于：

> 现代 Agent Framework 从来都不只是“模型 + 函数”

而是一个由配置层、运行层、上下文层、工具层和治理层共同组成的系统。

---

## 为什么要一直强调“理解设计”

课程又回到一个非常核心的工程师习惯：

很多教程会只告诉你：

```python
Runner.run(...)
```

然后就结束。

但真正的工程师应该继续追问：

> 为什么不是 `agent.run()`？

答案仍然是：

> 职责分离（Separation of Concerns）

也就是：

- Agent 负责能力描述
- Runner 负责生命周期与执行过程

这个原则不是 Agent 特有的，而是整个软件工程里都非常重要的设计思想。

一旦你开始主动问“为什么官方要多拆一个对象”，你就已经从 API 使用者转向框架理解者了。

---

## 项目正式升级：`agent-from-scratch`

这一课还宣布项目名和结构进一步升级，不再使用早期的简单练手目录，而是进入一个更像真实框架工程的项目：

```text
agent-from-scratch/
│
├── app.py
├── config.py
├── agent.py
├── runner.py
├── llm.py
├── tool_manager.py
├── tools/
│   ├── calculator.py
│   ├── filesystem.py
│   └── search.py
├── prompts/
│   └── system_prompt.txt
├── tests/
└── requirements.txt
```

这个结构的重要意义是：

- `agent.py`：定义 Agent
- `runner.py`：承载 Loop
- `llm.py`：统一模型抽象
- `tool_manager.py`：统一工具注册与执行
- `tools/`：存放具体工具实现
- `prompts/`：存放 Prompt 资源
- `tests/`：从一开始就为工程化留位置

这已经不是普通 Demo 结构，而是典型的“小型框架骨架”。

---

## 本周真正要掌握的五个问题

这一课给出了一个非常好的学习聚焦点：不要急着学 MCP、多 Agent、RAG，而要先把下面五个问题解释清楚。

### 1. 为什么 Agent 只是配置，而 Runner 才负责运行？

因为配置层和运行时层的职责不同，拆开更利于复用和扩展。

### 2. 为什么 Tool 需要 Schema？

因为 LLM 不认识 Python 函数，只认识结构化的工具描述。

### 3. 为什么 Agent Loop 本质是一个状态机？

因为系统在不同阶段会在“调用模型、接收响应、执行工具、结束”等状态之间流转。

### 4. 为什么要给 LLM 加一层抽象（LLM Interface）？

因为高层系统不应直接耦合具体模型厂商实现。

### 5. 为什么现代 Agent 都围绕 Responses API，而不是传统 Chat Completions？

因为 Agent 需要消费结构化事件，而不是只消费最终文本消息。

这五个问题如果真正理解了，后面扩展 Memory、MCP、多 Agent 时就不会迷失。

---

## 课程路线升级：按项目阶段推进

课程建议后续不再按“第 12 课、第 13 课”这种纯章节模式理解，而是按项目开发阶段推进。

### 第一阶段：Agent 核心（2 周）

- Python 工程结构
- Responses API
- Tool Calling
- Agent Loop
- Runner
- Session

最终成果：

> 一个可运行的单 Agent

### 第二阶段：工程能力（2 周）

- Memory
- Logging
- Tracing
- 配置管理
- 错误重试
- Token 管理

最终成果：

> 一个稳定的 Agent

### 第三阶段：高级能力（3 周）

- RAG
- MCP
- Multi-Agent
- 长任务（Long-running Agent）

最终成果：

> 一个接近 Claude Code 架构的 Agent

这说明课程已经完全从“学几个概念”切换为“做一个不断演进的系统”。

---

## Pair Programming 模式

这一课最后还把后续学习模式升级为更接近企业内带教的方式：

> Pair Programming（结对编程）

也就是每一节课都对应一个真实 Git Commit：

```text
commit 01：初始化项目
commit 02：实现 LLM 抽象层
commit 03：实现 Tool Manager
commit 04：实现 Runner
commit 05：实现 Agent Loop
...
```

这种方式的价值非常高：

- 每节课有真实产物
- 架构演进清晰可追踪
- 容易做 Code Review
- 最终可形成完整 GitHub 作品集

也更接近真实团队中的工程学习路径。

---

## 本课核心结论

### 1. 不要一上来先学 LangChain

更好的顺序是先理解 OpenAI SDK、Responses API、Agents SDK，再看高层封装。

### 2. `Agent` 不是机器人本体，而是配置层

它主要保存 Prompt、Model、Tools、Settings。

### 3. `Runner` 才是运行时核心

它内部承载的本质就是 Agent Loop。

### 4. 普通函数要变成 Tool，必须被 LLM 可理解

这就是为什么需要 `function_tool` 这类机制来生成 Schema。

### 5. 学习重点已经从“会调用 API”转向“会理解框架设计”

这才是成为 Agent Engineer 的关键。

---

## 下一步

从下一次开始，课程将正式进入结对编程和 Git Commit 驱动模式，逐步实现一个：

> 从零构建的 Agent Framework

并最终达到：

- 能看懂 OpenAI Agents SDK
- 能理解 Claude Code、OpenHands 等项目核心设计
- 能自己扩展 MCP、RAG、多 Agent 和生产级能力

