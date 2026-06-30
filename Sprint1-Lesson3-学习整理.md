# Sprint 1 - Lesson 3 学习整理

## 本节定位

这一节开始，我们正式进入整个 Agent 项目最关键的一步：

> 实现第一个真正可运行的 Agent Loop

前一节我们已经打通了这条链路：

```text
User
   │
   ▼
Runner
   │
   ▼
OpenAILLM
   │
   ▼
Responses API
```

但现在它还只是一个“能调模型”的程序，不是完整 Agent。

要让它真正成为 Agent，必须补上：

```text
LLM
↓
Tool Call
↓
执行 Tool
↓
Tool Result
↓
LLM
↓
Final Answer
```

也就是：

> `while True`

---

## 本节目标

真正实现下面这个最小闭环：

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
是否有 Tool Call？
  │
 ├── 否 → 返回最终答案
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
继续调用 LLM
```

这一节学完以后，你就拥有了一个真正意义上的最小 Agent。

---

## 本节核心知识点

### 1. 为什么 Agent 一定需要 Loop

因为 LLM 在第一次响应时，并不知道一次 Tool 调用能不能完成任务。

例如用户问：

```text
现在几点？
```

LLM 第一次可能返回：

```text
请调用 get_current_time
```

这还不是最终给用户的答案。

程序执行 Tool 后，还要把结果送回 LLM，例如：

```text
2026-06-30 21:30:00
```

然后 LLM 才能生成面向用户的自然语言回答：

```text
当前时间是 2026-06-30 21:30:00
```

所以：

- 第一次是决策
- 第二次才是总结

这就是为什么 Agent 天生需要循环。

---

### 2. 为什么 Runner 是 Loop 的宿主

Loop 是运行时行为，不是配置行为。

所以它必须属于：

```text
Runner
```

而不是：

```text
Agent
```

Agent 只描述：

- 我是谁
- 我有哪些 Tool
- 我用哪个 LLM

Runner 才负责：

- 调模型
- 判断返回类型
- 执行 Tool
- 继续循环
- 直到结束

所以这一节最重要的架构结论依然是：

> Agent 是配置，Runner 是运行时。

---

### 3. 最小 Agent Loop 长什么样

这一节最核心的伪代码可以写成：

```python
while True:
    response = llm.generate(...)

    if response 里有 tool call:
        执行 tool
        把结果追加回消息列表
        continue

    return 最终答案
```

如果你把这段逻辑真正理解了，后面看 OpenAI Agents SDK、LangGraph、Claude Code、OpenHands 的源码都会轻松很多。

因为它们本质上都绕不开这段循环。

---

## 本节实现思路

为了让这一节聚焦在 Loop 本身，我们先只支持一个 Tool：

```python
get_current_time()
```

并只做一件最小的事情：

- LLM 如果要求调用这个 Tool
- Python 就执行它
- 然后把结果回给 LLM
- 再拿最终答案

这足够让整个闭环成立。

---

## 本节建议代码结构

这一节会涉及下面几个位置：

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

### `runner.py`

这里是本节主角，负责：

- 组装消息
- 调 LLM
- 识别 Tool Call
- 执行 Tool
- 回传 Tool Result
- 结束循环

---

## 一个建议的最小运行流程

### Step 1

用户输入：

```text
现在几点？
```

### Step 2

Runner 组织消息：

```python
messages = [
    {"role": "system", "content": agent.instructions},
    {"role": "user", "content": user_input},
]
```

### Step 3

调用：

```python
response = agent.llm.generate(messages, tools=agent.tools)
```

### Step 4

判断 `response.output` 里面有没有 `function_call`

如果有：

- 解析函数名
- 解析参数
- 执行对应 Tool

### Step 5

把 Tool Result 再追加回消息中，例如：

```python
messages.append(...)
```

### Step 6

再次调用 LLM，拿到最终自然语言答案

---

## Code Review 视角

### 不推荐的写法

```python
if "时间" in user_input:
    result = get_current_time()
```

这其实不是 Agent，而是手写 Workflow。

因为决策发生在 Python 里，而不是 LLM 里。

### 推荐的写法

```python
response = llm.generate(...)
```

然后由模型决定是否调用 Tool。

这才符合 Agent 的核心思想：

> 由 LLM 决策，由 Python 执行。

---

## 官方框架怎么做

OpenAI Agents SDK 表面上会把这些细节封装成：

```python
Runner.run(...)
```

但它的本质仍然是：

```python
while True:
    response = llm.generate(...)
    if tool_call:
        execute_tool(...)
        continue
    return answer
```

只不过官方额外帮你做好了：

- 更完整的消息组织
- Tool 注册机制
- 更标准的结果回传
- 错误处理
- Tracing
- Session

所以：

> 框架不是换了一套原理，而是把同一套原理工程化了。

---

## 本节最重要的一句话

> Tool Calling 不是“模型直接执行工具”，而是“模型提出调用请求，Runner 负责把它真正执行掉”。

这句话必须非常牢。

因为后面无论是 MCP、RAG、多 Agent，底层都还是这个分工。

---

## 本节作业

### 任务 1

在项目里实现：

```python
get_current_time()
```

### 任务 2

在项目里实现：

```python
time_schema
```

### 任务 3

在 `Runner.run()` 中写出第一版最小 Loop：

```python
while True:
    ...
```

### 任务 4

让程序至少能完成这类对话：

```text
用户：现在几点？
Agent：当前时间是 ...
```

---

## 本节 Git Commit

建议提交信息：

```text
Implement minimal agent loop
```

---

## 下一步

下一节建议进入：

> 多 Tool 支持

也就是把现在只支持一个时间 Tool，升级成：

- `get_current_time`
- `calculator`
- `read_file`

这样项目会从“最小 Agent”进入“真正开始像 Agent”的阶段。

