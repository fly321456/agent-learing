# 第五课学习整理：写出第一个 Agent（第一版）

## 本课定位

从这一课开始，正式进入真正的 Agent 开发阶段。

这一课的关键，不只是“会写一个 Tool”，而是建立一个对 Agent Framework 开发者非常重要的认知：

> Agent 的核心，不是某个神秘 SDK，而是一个不断调用 LLM、判断是否需要执行 Tool、再把结果送回 LLM 的循环。

也可以用一句更直接的话概括：

> Agent 本质上就是一个 `while` 循环。

---

## 本课目标

本课要实现的流程是：

```text
             用户
               │
               ▼
        "18 × 29 等于多少？"

               │
               ▼
        OpenAI Responses API
               │
               ▼
     LLM 判断需要 calculator Tool
               │
               ▼
      Python 执行 calculator()
               │
               ▼
           返回计算结果
               │
               ▼
     LLM 组织最终自然语言回答
               │
               ▼
              用户
```

这个流程已经具备了一个最小 Agent 的闭环结构。

---

## 第一步：先写 Tool

本课的第一个 Tool 仍然选择最简单的：

> `calculator`

示例函数如下：

```python
def calculator(expression: str):
    """
    执行数学表达式
    """

    return eval(expression)
```

从纯 Python 角度看，这个函数非常简单。

这也正说明了一个很重要的事实：

> Tool 的执行逻辑往往不复杂，真正关键的是怎样把 Tool 介绍给 LLM。

也就是说，Agent 难点通常不在“函数本身多难写”，而在：

- 如何定义 Tool 能力
- 如何向模型描述 Tool
- 如何在循环里调用 Tool

---

## 第二步：定义 Tool Schema

如果只是写了一个 Python 函数，模型仍然不知道：

- 这个 Tool 叫什么
- 什么时候该调用它
- 需要传什么参数
- 参数是什么类型

所以必须定义 Schema。

示例：

```python
calculator_schema = {
    "type": "function",
    "name": "calculator",
    "description": "计算数学表达式，例如18*29",
    "parameters": {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string"
            }
        },
        "required": ["expression"]
    }
}
```

这里有一个非常重要的理解：

> Schema 里没有业务逻辑，只有“给模型看的说明书”。

它的职责不是计算，而是帮助 LLM 判断：

> 当前这个问题是不是应该调用 `calculator`

---

## 为什么 Schema 这么重要

如果只告诉别人：

```text
工具名：calculator
```

大多数人并不知道这个工具具体怎么用。

但如果你补充完整说明：

```text
名字：calculator
用途：计算数学表达式
参数：expression
示例：18*29
```

那使用方式就会立刻清晰很多。

LLM 也是一样。

所以 Schema 的本质可以继续强化为：

> 给 LLM 的说明书

或者更工程化一点说：

> 一份供模型消费的工具接口文档

---

## 第三步：初始化 OpenAI Client

在 `config.py` 中，可以先完成最小客户端初始化：

```python
from openai import OpenAI
import os

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)
```

这一层的重点不是代码量，而是职责清晰：

- `config.py` 负责连接模型服务
- 业务流程不要写在配置文件里

同时也体现出一个工程优势：

未来如果切换兼容接口的模型服务，通常只需要调整少量配置，而不必重写整个 Agent 主逻辑。

---

## 第四步：第一次请求 LLM

真正进入 Agent 交互的起点，是向 Responses API 发起请求，并把 Tool Schema 一起告诉模型。

例如：

```python
response = client.responses.create(
    model="gpt-5",
    input="18*29是多少？",
    tools=[
        calculator_schema
    ]
)
```

这里最关键的一行是：

```python
tools=[calculator_schema]
```

它的含义是：

> 告诉模型：你现在可以使用 `calculator` 这个 Tool

如果不传 Tool Schema，模型就不知道这个工具存在，也无法稳定地产生 Tool Call。

---

## 第一次返回的本质是什么

很多初学者会以为这次请求会直接得到最终答案：

```text
522
```

但对一个真正开启 Tool Calling 的 Agent 来说，第一次返回更可能是：

```json
{
  "type": "function_call",
  "name": "calculator",
  "arguments": {
    "expression": "18*29"
  }
}
```

这意味着：

> 模型并没有亲自计算

它只是给出了一个决策：

> 我建议调用 `calculator("18*29")`

这一步非常关键，因为它再次证明：

> LLM 负责决策，不负责执行

---

## 第五步：由 Python 执行 Tool

程序拿到 Tool Call 后，才会真正执行本地函数：

```python
result = calculator("18*29")
```

得到：

```text
522
```

这一步发生在 Python 世界，而不是 LLM 世界。

因此必须始终区分：

- 模型只是提出调用建议
- 真正执行动作的是宿主程序

---

## 第六步：把 Tool Result 回传给 LLM

很多新人会在执行完 Tool 后就停止。

但实际上这还没有结束，因为模型还不知道工具执行结果是什么。

所以还要把结果重新发回给 LLM：

```text
Tool Result:
522
```

模型收到这个结果后，才会生成最终自然语言回答，例如：

> 18 × 29 等于 522。

所以一个带 Tool Calling 的最小 Agent，通常不是“一次请求就结束”，而是至少包含两段交互：

### 第一轮

```text
用户
↓
LLM
↓
Tool Call
```

### 第二轮

```text
Tool Result
↓
LLM
↓
Final Answer
```

这也是很多教程最容易讲得过于简化的地方。

---

## Agent Loop 的最小形态

到这里，就能看到 Agent 的核心控制流了。

伪代码如下：

```python
while True:

    response = LLM()

    if response 是 ToolCall:
        执行 Tool
        Tool Result 发回 LLM
    else:
        break
```

这段结构虽然简单，但意义非常大。

因为以后你看到的很多系统，本质都是在这个循环基础上做扩展：

- 多 Tool
- 多轮推理
- Memory
- Streaming
- Retry
- Parallel Tool Calling

也就是说：

> 复杂框架并没有改变核心原理，只是在这个最小循环上不断增强能力。

---

## 为什么 Agent 不应该写成大量 `if...else`

传统程序的直觉写法常常是：

```python
if question 包含 天气:
    weather()

if question 包含 数学:
    calculator()
```

这种写法的问题在于，它本质还是规则驱动程序。

真正的 Agent 应该是：

```python
while True:
    response = LLM()

    if ToolCall:
        Execute Tool
        Continue
    else:
        Finish
```

也就是说：

- 工具选择不是程序员手写规则
- 工具选择由模型根据上下文做决策

这就是 Agent 与传统 Workflow 式程序的本质区别之一。

---

## 本课最重要的认知升级

第五课真正要建立的新认知是：

> Agent 不是“调用一次 LLM 获得答案”

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
Finish
```

这意味着：

- LLM 不是单次调用
- Tool 不是可有可无的附件
- Agent 是一个持续协作过程

这也是“会用 AI”和“会开发 Agent”之间最关键的分界线之一。

---

## 工程实践建议

从这一课开始，课程建议同步建立一个 GitHub 仓库，例如：

```text
my-agent-learning/
```

并按课程节奏提交 Commit，例如：

```text
lesson-01-agent-thinking
lesson-02-tool-calling
lesson-03-project-structure
lesson-04-schema
lesson-05-first-agent
```

这样长期收益很大：

- 有清晰学习轨迹
- 有可展示的作品集
- 便于后续回顾每一步的认知变化

---

## 下一课预告

下一课将进入真正的完整编码实现，包括：

- 使用 OpenAI Responses API 发起完整请求
- 解析返回的 Tool Call
- 执行本地 Python Tool
- 把 Tool 结果回传给 LLM
- 实现一个真正可运行的 Agent Loop

到那时，就会拥有第一个真实可运行的 Agent 雏形。

