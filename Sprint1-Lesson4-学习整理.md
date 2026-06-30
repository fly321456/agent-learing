# Sprint 1 - Lesson 4 学习整理

## 本节定位

上一节我们已经完成了最关键的一步：

> 写出第一个真正可运行的 Agent Loop

但上一节的系统还有一个明显限制：

> 只适合支持一个 Tool，或者只能用非常临时的方式处理 Tool

这意味着它还不能真正叫做“可扩展 Agent”。

所以这一节要解决的问题是：

> 如何让 Agent 从“支持一个 Tool”升级到“支持多个 Tool”

也就是说，这一节开始进入真正的：

> Tool Manager 思维

---

## 本节目标

把项目从“只能跑一个最小 Tool 闭环”，升级成“可以管理多个 Tool 的最小 Agent”。

这一节期望的能力是：

```text
用户：现在几点？
Agent：调用 get_current_time

用户：18 * 29 等于多少？
Agent：调用 calculator
```

也就是说，同一个 Runner，不再只会处理单个 Tool，而是开始具备：

- Tool 注册
- Tool 查找
- Tool 执行

这就是后面所有 Tool 扩展的基础。

---

## 本节核心知识点

### 1. 为什么不能把 Tool 执行写死在 Runner 里

很多新人在这个阶段很容易写出这样的代码：

```python
if tool_name == "get_current_time":
    result = get_current_time()
elif tool_name == "calculator":
    result = calculator(...)
```

这在功能上当然能跑，但它会导致一个非常严重的问题：

> 每增加一个 Tool，就要改 Runner

这意味着：

- Runner 同时负责运行
- Runner 还负责知道所有 Tool
- Runner 还负责做工具路由

这会导致 Runner 越来越臃肿。

而一个成熟的 Agent 系统应该做到：

> 新增 Tool 时，尽量不改 Runner

---

### 2. Tool Manager 为什么会出现

当 Tool 数量开始增加时，系统就必须有一个单独模块负责：

- 注册 Tool
- 保存 Tool
- 根据名字查找 Tool
- 执行 Tool

这就是：

```text
Tool Manager
```

它的出现不是为了“显得架构高级”，而是因为：

> Tool 一多，不拆出来就一定会乱

所以这一节要开始建立的不是“写几个工具函数”的思维，而是：

> 管理工具系统

---

### 3. Tool 在工程里至少分成两层

这一节最重要的认知之一是：

一个 Tool 在工程层面至少分两层：

### 第一层：执行逻辑

例如：

```python
def get_current_time():
    ...

def calculator(expression):
    ...
```

### 第二层：给 LLM 的 Schema

例如：

```python
time_schema = {...}
calculator_schema = {...}
```

所以 Tool Manager 最后要管理的，其实不是“只有函数”，而是：

- 函数实现
- schema 描述
- 名字到实现的映射关系

这也是后面为什么很多框架会专门设计 Tool 对象，而不是只存函数。

---

## 本节推荐的最小设计

这一节为了保持项目简单，我们先不一步做到“完整 Tool 类”，而是先用一个非常实用的中间形态：

### 方案：用字典管理 Tool

例如：

```python
tools = {
    "get_current_time": get_current_time,
    "calculator": calculator,
}
```

再配合：

```python
schemas = [
    time_schema,
    calculator_schema,
]
```

这样我们就已经拥有了最小的 Tool 注册机制。

这一版虽然简单，但已经足够支撑：

- 多 Tool
- 基于名字执行 Tool
- 基于 Schema 暴露 Tool 给 LLM

这是一种非常好的第一版工程策略：

> 先做最小可扩展形态，再逐步面向对象化

---

## 本节建议增加的 Tool

这一节建议在项目里加入第二个 Tool：

```python
calculator(expression)
```

为什么选它？

因为它和 `get_current_time()` 很不一样：

- `get_current_time` 没参数
- `calculator` 有参数

这样一来，系统就会第一次真正面对：

- 无参 Tool
- 有参 Tool

这对于理解 Tool Schema 和 Tool Execution 都非常关键。

---

## 本节的最小运行逻辑

现在 Runner 的核心流程开始变成：

### Step 1

把所有 schema 传给 LLM：

```python
response = llm.generate(messages, tools=schemas)
```

### Step 2

如果发现 `function_call`

就取出：

- `tool_name`
- `arguments`

### Step 3

从 Tool Manager 或 Tool 字典里找到对应函数：

```python
tool_fn = tools[tool_name]
```

### Step 4

执行：

```python
result = tool_fn(...)
```

### Step 5

把结果回传给 LLM，继续 Loop

这个时候你会发现：

> Runner 的本质没变，只是 Tool 执行从“写死”变成了“查表”

这一步在架构上非常重要。

---

## Code Review 视角

### 不推荐的写法

```python
if tool_name == "get_current_time":
    result = get_current_time()
elif tool_name == "calculator":
    result = calculator(arguments["expression"])
elif tool_name == "read_file":
    ...
elif tool_name == "search":
    ...
```

为什么不推荐？

因为：

- 每加一个 Tool 就得改 Runner
- Runner 被迫知道所有 Tool 细节
- Tool 数量一多就会膨胀

这违反了单一职责原则。

### 更推荐的方向

```python
tool_fn = tool_registry[tool_name]
result = tool_fn(...)
```

这样：

- Runner 不关心 Tool 细节
- Runner 只负责调度
- Tool 增减对 Runner 的影响最小

这就是更接近框架设计的写法。

---

## 官方框架怎么做

官方或成熟框架通常不会把 Tool 处理写成一串 `if/elif`。

它们一般都会有某种形式的：

- Tool Registry
- Tool Manager
- Tool Object

本质上做的事情都差不多：

```text
工具名
↓
找到工具
↓
执行工具
↓
拿到结果
```

只是框架会把这套逻辑封装得更规范、更完整。

所以这一节你学到的不是“小技巧”，而是：

> 所有 Agent Framework 都绕不开的工具分发机制

---

## 本节最重要的一句话

> 当 Tool 数量大于 1 时，Runner 就不应该继续手写工具分支，而应该开始依赖 Tool Registry / Tool Manager。

这句话非常关键。

因为它标志着系统开始从“能跑”走向“能扩展”。

---

## 本节作业

### 任务 1

新增第二个 Tool：

```python
calculator(expression)
```

### 任务 2

新增：

```python
calculator_schema
```

### 任务 3

用一个最小字典或注册表保存 Tool：

```python
tool_registry = {
    ...
}
```

### 任务 4

修改 Runner，让它不要再手写多个 Tool 分支，而是：

```python
按 tool_name 查找并执行
```

### 任务 5

让项目至少支持这两类请求：

```text
现在几点？
18 * 29 等于多少？
```

---

## 本节 Git Commit

建议提交信息：

```text
Add multi-tool support
```

---

## 下一步

下一节建议进入：

> 抽出真正的 `ToolManager`

也就是把这一节用字典实现的最小 Tool Registry，再正式收敛成独立模块。

这样整个项目会继续朝着：

```text
Agent
+ 
Runner
+ 
LLM Interface
+ 
Tool Manager
```

的框架形态演进。

