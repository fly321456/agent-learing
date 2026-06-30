# 第12课学习整理：写出第一个真正的 Agent（100 行以内）

## 本课定位

从这一课开始，课程正式进入：

> 真正的实战阶段

这一课第一次明确要求：

> 不依赖任何 Agent 框架，自己实现一个最小可运行 Agent

这意味着目标已经不是“理解 Agent 概念”，而是开始亲手搭出最核心的运行闭环。

本课限制也非常明确：

- 不用 LangChain
- 不用 CrewAI
- 不用 AutoGen
- 不用 OpenAI Agents SDK

只使用：

- Python
- OpenAI SDK
- Responses API

这样做的原因非常关键：

> 如果自己不会实现最小 Agent，后面再看任何框架源码都会很吃力

---

## 本课目标

这一课最终要实现的最小交互流程是：

```text
用户输入：
今天北京天气怎么样？

程序流程：
LLM
↓
决定调用 weather Tool
↓
Python 执行 Tool
↓
得到结果
↓
LLM 整理自然语言
↓
输出答案
```

虽然示例任务看起来简单，但背后已经包含了现代 Agent 的最关键闭环：

- 模型决策
- 工具执行
- 结果回传
- 模型总结

课程刻意把目标控制在大约 100 行以内，是为了逼自己真正看懂每一部分，而不是被大段样板代码淹没。

---

## 项目结构

这一课把最小项目结构定义为：

```text
agent-from-scratch/

├── app.py
├── config.py
├── tools.py
├── schemas.py
├── agent.py
├── .env
└── requirements.txt
```

这是一个比前面“纯理论阶段”更轻量、也更适合最小实现的目录结构。

这里最重要的不是文件多少，而是职责开始清晰分层：

- `tools.py`：工具实现
- `schemas.py`：工具的模型可理解描述
- `agent.py`：最小 Agent 行为
- `config.py`：配置
- `app.py`：入口

---

## 第一步：不要先写 Agent，先写 Tool

这一课特别纠正了一个初学者常见习惯：

很多人一开始就写：

```python
class Agent:
```

课程明确指出，这不是最好的起点。

更合理的顺序应该是：

> 先写 Tool

原因非常简单：

> Agent 的能力全部来自 Tool

没有 Tool，Agent 只是一个空壳，根本谈不上执行能力。

---

## `tools.py`：先实现最简单的 Tool

这一课先从一个最小、可验证、无外部依赖的 Tool 开始：

```python
from datetime import datetime

def get_current_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
```

这段代码非常短，也正说明了一个重要事实：

> Tool 的 Python 实现常常很简单

真正让 Agent 变复杂的，不是函数本身，而是：

- 模型如何知道它存在
- 模型如何知道该什么时候调用它
- 程序如何把执行结果再送回模型

---

## 第二步：Schema 让 LLM 理解 Tool

因为 LLM 并不认识 Python 函数本身，所以必须额外提供工具描述。

例如：

```python
time_schema = {
    "type": "function",
    "name": "get_current_time",
    "description": "获取当前时间",
    "parameters": {
        "type": "object",
        "properties": {}
    }
}
```

这里最重要的理解是：

> Schema 里没有 Python 执行逻辑，只有给 LLM 看的工具说明

也就是说，Schema 解决的是：

- 这个 Tool 叫什么
- 这个 Tool 是干什么的
- 调用它需要哪些参数

这再次验证了前面课程反复强调的一点：

> LLM 不认识函数实现，只认识结构化工具描述

---

## 第三步：现在才开始写 Agent

这一课对 Agent 的职责做了非常简洁的收束：

一个最小 Agent 在第一版里，其实只做两件事：

```text
调用模型
执行 Tool
```

这比很多初学者想象得简单得多。

一开始不需要急着把 Memory、Retry、Tracing、Session 等复杂能力全部塞进去。

先把最小闭环跑通，才是最重要的。

---

## 第一个最小版本：只支持一次 Tool 调用

课程先给出一个简化版思路：

```python
response = ask_llm()

if Tool:
    execute()
else:
    print(answer)
```

这个版本的意义不在于最终形态，而在于：

> 先把“模型决策 -> 工具执行”这个最小链路打通

它只支持一次 Tool 调用，但对于理解 Agent 的第一版已经足够。

---

## 第五步：升级到真正的 Agent Loop

当最小版本理解清楚之后，就可以自然升级成完整的最小 Loop：

```python
while True:

    response = ask_llm()

    if Tool:
        execute()
        continue
    else:
        break
```

这一段就是本课的灵魂。

课程再次强调：

> 整个 Agent 的核心，其实就是 `while True`

因为这段循环背后代表的是：

- 不断获取模型事件
- 判断是否需要工具
- 执行工具
- 把结果送回模型
- 继续直到完成

这也是为什么前面课程一直强调：

> Agent Loop 才是 Agent 的灵魂

---

## 为什么所有框架都绕不开循环

这一课用 Claude Code 式任务举了一个很好的例子：

用户要求修复 Bug，实际过程可能是：

```text
读文件
↓
搜索错误
↓
修改代码
↓
运行测试
↓
测试失败
↓
继续修改
```

这本质上始终是：

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
```

而不是：

```text
LLM
↓
结束
```

所以循环不是“为了代码优雅”，而是：

> Agent 天生需要循环

这是任务本质决定的，而不是工程师个人风格问题。

---

## 为什么这一课仍然不用 OpenAI Agents SDK

很多人会问，既然官方已经提供：

```python
Runner.run()
```

为什么还要自己写？

这一课给出的答案非常重要：

> 因为以后当你打开官方源码，看到内部的 `while True`，你会真正看懂它

换句话说：

学习框架最大的误区不是“不会用”，而是：

> 只会调用，不会实现

而自己手写一个最小 Agent，可以直接把框架从“黑盒”变回“白盒”。

---

## 本课真正学到的软件设计思想

这一课最值得记住的一句话是：

> 框架不是魔法，它只是把你会写的代码封装起来

例如我们今天自己写的是：

```python
while True:
    ...
```

而官方框架对外提供的是：

```python
Runner.run()
```

两者本质上一样，只是官方额外帮你封装了：

- Retry
- Logging
- Tracing
- Memory
- Streaming

也就是说，框架做的不是“创造新原理”，而是“把已有原理工程化”。

---

## 本课的小练习

这一课给出的动手练习非常聚焦，只要求先完成三个小文件，不追求一次做大：

### `tools.py`

实现：

```python
get_current_time()
```

### `schemas.py`

实现：

```python
time_schema
```

### `agent.py`

先写出最小类骨架：

```python
class Agent:

    def __init__(self):
        ...

    def ask_llm(self):
        ...

    def execute_tool(self):
        ...

    def run(self):
        ...
```

这里最关键的要求不是“立刻功能完整”，而是：

> 先建立框架边界，再逐步填实现

这非常符合真实工程开发方式。

---

## Pair Programming 与 Sprint 模式

这一课还进一步升级了后续学习方式：

后面不再是单纯“下一课继续听”，而是进入：

- 需求提出
- 一起设计
- 先尝试实现
- 再做 Code Review
- 最后分析哪些设计符合 Agent 思维

也就是更接近真实团队的：

> Pair Programming

同时，课程节奏也建议从“课时制”转向“迭代制”：

- Sprint 1：实现最小 Agent
- Sprint 2：加入多 Tool
- Sprint 3：加入 Memory
- Sprint 4：支持 MCP
- Sprint 5：支持 Multi-Agent
- Sprint 6：对标 OpenAI Agents SDK

这代表课程已经彻底从“知识学习”转向“工程交付”。

---

## 本课核心结论

### 1. 第一个真正的 Agent 不需要很多代码

100 行左右就足够实现最小闭环。

### 2. 先写 Tool，再写 Agent

因为 Agent 的能力根源来自 Tool。

### 3. Schema 是给 LLM 看的说明书

它让模型理解 Tool，而不是执行 Tool。

### 4. Agent 的灵魂是 `while True`

真正让系统成为 Agent 的，是循环式决策和执行，而不是某个类名。

### 5. 自己实现最小 Agent，是理解框架源码最好的准备

这样以后看到官方的 `Runner.run()`，就不会再觉得神秘。

---

## 下一步

从后续阶段开始，课程将真正进入结对编程式实战推进：

- 写代码
- 做 Code Review
- 分析架构选择
- 按 Sprint 逐步演进项目

也就是说，这一课是“从理解 Agent 过渡到开发 Agent”的真正分水岭。

