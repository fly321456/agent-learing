# 第八课学习整理：真正开始写 Agent（第一个版本）

## 本课定位

从这一课开始，课程进入新的训练模式：

> ① 原理 → ② 自己实现 → ③ 分析官方源码 → ④ 总结设计思想

这意味着目标已经不只是“学会调用 API”，而是开始按 Agent Engineer 的方式思考：

- 先理解运行原理
- 再自己实现最小系统
- 再对照官方框架设计
- 最后提炼成可复用的工程思想

第八课的真正主题是：

> 开始把 Agent 当成一个运行中的系统，而不是几个函数拼起来的脚本

---

## 本课目标

本课的目标不是立刻写出完整代码，而是先把“第一个真正可工作的 Agent Loop”设计清楚。

核心问题是：

> 一个 Agent 为什么一定要有循环？

---

## 第一步：为什么 Agent 一定要有 `while`

很多初学者会下意识写出这样的逻辑：

```python
response = llm()

if tool:
    execute()
```

然后就结束。

这种写法的问题在于，它默认假设：

> 一次 Tool 调用就能完成任务

但真实世界里的 Agent 任务通常不是这样。

例如用户说：

> 帮我分析这个 GitHub 项目

模型第一次可能决定：

```text
调用 git_clone
```

这显然没有完成任务。

第二次可能决定：

```text
读取 README
```

还是没有完成。

第三次可能是：

```text
读取 pom.xml
```

第四次可能是：

```text
搜索 Redis
```

直到最后模型才会判断：

```text
我已经分析完成
```

所以 Agent 的真实结构不是：

```text
LLM
↓
Tool
↓
结束
```

而是：

```text
LLM
↓
Tool
↓
LLM
↓
Tool
↓
LLM
↓
Tool
↓
……
↓
Finish
```

这节课的第一个原则因此可以明确写成：

> Agent 在开始执行前，并不知道自己要循环多少次

这正是 Agent 和传统 Workflow 的本质区别之一。

---

## 第二步：把 Agent 看成状态机

所有现代 Agent，本质上都可以建模成状态机。

最小状态流转可以画成：

```text
        START
          │
          ▼
    CALL MODEL
          │
          ▼
 RECEIVE RESPONSE
          │
          ▼
  是否有 Tool Call？
      │          │
      │Yes       │No
      ▼          ▼
 EXECUTE TOOL   FINISH
      │
      ▼
 TOOL RESULT
      │
      ▼
 CALL MODEL
```

这里没有任何神秘能力，只有状态切换。

Agent 的核心不是“模型有多聪明”，而是：

> 系统如何在这些状态之间稳定流转

这也是后面所有 Agent Framework 设计抽象的起点。

---

## 第三步：最小伪代码

如果先不关心具体 SDK，只保留最核心控制逻辑，可以写成：

```python
while True:

    response = ask_llm()

    if response.type == "tool_call":
        result = execute_tool()
        send_result_back()
    else:
        break
```

这段伪代码虽然简单，但已经暴露了 Agent 的本质：

- 收到模型事件
- 判断事件类型
- 如果需要工具，就执行
- 再把结果送回模型
- 否则结束

看到这里，就应该逐步建立一种新的联想：

> Agent 很像操作系统、GUI 程序或 Node.js 中的事件循环

因为它们共同遵循的都是：

```text
收到事件
↓
处理事件
↓
等待下一个事件
```

所以 Agent 不只是“多轮调用模型”，更像一个围绕事件驱动的运行时系统。

---

## 第四步：不要再把 Agent 当成一个整体黑盒

从这一课开始，Agent 必须被拆开来看。

一个更接近现代框架视角的 Agent，至少可以拆成：

```text
Agent

├── LLM
├── Tool Manager
├── Memory
├── Planner
├── Runner
└── Session
```

这些模块分开设计，不是为了显得高级，而是因为它们职责不同。

例如：

### Tool Manager

负责：

- 有哪些 Tool
- 如何查找 Tool
- 如何执行 Tool

### Memory

负责：

- 历史消息
- 长期记忆
- 用户信息

### Runner

负责：

- 驱动整个 Loop
- 调度模型与工具
- 管理运行状态

也就是说，到了这个阶段，Agent 已经越来越像一个真正的框架，而不是一个演示脚本。

---

## 第五步：我们自己设计 Runner

很多教程直接给你一个：

```python
agent.run()
```

看起来很方便，但容易隐藏真正的核心。

这一课特意把运行逻辑单独拿出来，设计成：

```python
runner.run(user_input)
```

为什么这样更合理？

因为 `Runner` 的职责非常明确：

```text
接收用户输入
↓
调用模型
↓
发现 Tool Call
↓
执行 Tool
↓
继续调用模型
↓
直到结束
```

所以以后看到：

```python
Runner.run()
```

脑子里应该自动翻译为：

```python
while True:
```

也就是说：

> Runner 不是一个“辅助对象”，而是 Agent Loop 的宿主

---

## 第六步：为什么官方要设计 Runner

这一课已经开始进入“分析官方源码思想”的阶段。

问题是：

为什么不直接写成：

```python
agent.run()
```

而是倾向于：

```python
Runner.run(agent)
```

核心原因在于职责分离。

### Agent

负责：

- 定义能力
- 持有 Prompt
- 持有 Tool 集合
- 定义行为边界

### Runner

负责：

- 真正运行 Loop
- 驱动状态流转
- 管理执行过程

这样设计的好处是，一个 Runner 在理论上可以运行多个 Agent：

- Agent A
- Agent B
- Agent C

甚至进一步支持：

- Multi-Agent
- 嵌套 Agent
- 编排式 Agent 系统

这体现的是非常经典的软件设计原则：

> 单一职责原则（Single Responsibility Principle）

优秀 Agent 框架之所以看起来清晰，很大程度上就是因为它们把“能力定义”和“运行执行”拆开了。

---

## 第七步：真正的 Agent 思维

这一课最值得反复记住的一句话是：

> Agent 不是一个对象，而是一个运行中的系统

很多新人会以为：

```python
agent = Agent()
```

只要实例化了，Agent 就已经“存在”了。

但从运行时视角看，真正工作的 Agent 不只是一个类实例，它还包含：

- 当前 Prompt
- 当前 Memory
- 当前 Tool 集合
- 当前 Session
- 当前 State
- 当前 Loop

也就是说：

> Agent 更接近 Runtime（运行时），而不是单纯的 Python 类

这个认识非常关键，因为它会直接影响你后面如何理解：

- Session
- Runner
- State
- Checkpoint
- Memory
- Multi-Agent Coordination

一旦把 Agent 错看成“一个对象”，就很难理解现代框架为什么要设计那么多运行时组件。

---

## 本课最重要的三个结论

### 1. Agent 是状态机

它不是一个普通函数调用链，而是多个状态之间持续切换的系统。

### 2. Runner 是 Agent Loop 的真正宿主

真正执行循环、调度模型与工具的，通常不是 Agent 自身，而是 Runner。

### 3. Agent 是 Runtime

它不只是一个类定义，而是包含上下文、状态、工具、记忆和循环在内的运行时系统。

---

## 课后思考题

如果让你自己设计一个 Agent Framework，下面这些能力应该放在哪一层？

```text
读取文件
联网搜索
记录聊天历史
执行整个循环
决定是否调用 Tool
保存用户信息
```

这个题目的真正目的，是训练你建立“模块边界感”。

也就是：

- 什么属于 Tool 层
- 什么属于 Memory 层
- 什么属于 Runner 层
- 什么属于模型决策层

这是从“会写功能”走向“会设计框架”的关键一步。

---

## 下一步

从下一课开始，将直接对标 OpenAI Agents SDK 的核心抽象，逐步实现：

```text
lesson-09

├── Agent
├── Runner
├── Tool
├── Session
└── Result
```

当亲手做完这一版之后，再去看官方 SDK 或其他 Agent 框架源码，会明显发现：

> 它们并不神秘，只是在更系统地组织同一套运行时逻辑

