# Sprint 1 - Lesson 5 学习整理

## 本节定位

上一节我们已经让 Agent 从“单 Tool”升级成了“多 Tool”。

但上一节的实现还有一个非常明显的问题：

> Tool 注册、Tool 查找、Tool 执行，仍然散落在 Runner 周边

这意味着系统虽然已经比前面更强了，但还不够“像框架”。

所以这一节要做的事情非常明确：

> 正式抽出 `ToolManager`

这会是项目第一次从“功能可用”迈向“职责清晰”的关键架构升级。

---

## 本节目标

把上一节的：

- Tool 字典
- Schema 列表
- Tool 执行逻辑

从 Runner 周边收拢到一个独立模块中，让项目形成下面这条更清晰的运行链路：

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
ToolManager
  │
  ├── 提供所有 tool schema 给 LLM
  ├── 根据 tool name 查找工具
  └── 执行工具
```

这一节学完以后，Runner 会真正开始像“运行时调度器”，而不是“所有逻辑都自己做”的脚本控制器。

---

## 本节核心知识点

### 1. 为什么 Tool Registry 还不够

上一节我们已经引入了最小注册表思维，例如：

```python
tool_registry = {
    "get_current_time": get_current_time,
    "calculator": calculator,
}
```

这已经比一长串 `if/elif` 更好。

但它仍然存在几个问题：

- Tool Schema 可能还在别处维护
- Tool 执行逻辑可能还要单独写参数处理
- Runner 仍然知道“如何找 Tool”
- Runner 仍然容易开始知道“如何执行 Tool”

也就是说：

> Registry 只是第一步，Manager 才是真正的模块化边界

---

### 2. ToolManager 的职责应该是什么

这一节最关键的问题不是“怎么写类”，而是“它到底该负责什么”。

一个最小 `ToolManager` 至少应该负责三件事：

### 1. 注册工具

例如：

```python
register(name, func, schema)
```

### 2. 提供 schema 给 LLM

例如：

```python
get_schemas()
```

### 3. 按名称执行工具

例如：

```python
execute(tool_name, arguments)
```

这三件事如果都收进 ToolManager，Runner 就可以明显瘦下来。

---

### 3. 为什么 ToolManager 是架构分层，不是“多写一个类”

很多初学者看到这一步会觉得：

> 用字典也能跑，为什么还要多封装一层？

这是一个很典型的工程思维分水岭。

因为真正的项目不会永远停留在两个 Tool：

- `get_current_time`
- `calculator`

后面很快会扩展到：

- `read_file`
- `search`
- `run_python`
- `run_shell`
- `git_status`
- `browser_search`

如果没有 ToolManager，后续所有这些能力都会不断泄漏进 Runner。

所以：

> ToolManager 的出现，不是为了“代码更好看”，而是为了防止职责失控。

---

## 本节推荐的最小 ToolManager 设计

这一节建议先做一个非常朴素但正确的版本：

```python
class ToolManager:
    def __init__(self):
        self.tools = {}
        self.schemas = []
```

然后提供三个核心方法：

### `register_tool`

```python
def register_tool(self, name, func, schema):
    ...
```

### `get_schemas`

```python
def get_schemas(self):
    ...
```

### `execute`

```python
def execute(self, tool_name, arguments):
    ...
```

这一版已经足够让整个系统具备最小的工具管理能力。

注意：

> 本节重点是职责收拢，不是追求一次把 Tool 系统设计到极致

---

## 本节 Runner 会发生什么变化

上一节的 Runner 可能还像这样：

```python
response = llm.generate(messages, tools=schemas)
...
tool_fn = tool_registry[tool_name]
result = tool_fn(...)
```

这一节之后，Runner 的思路应该变成：

```python
response = llm.generate(messages, tools=tool_manager.get_schemas())
...
result = tool_manager.execute(tool_name, arguments)
```

这个变化非常重要。

它意味着：

- Runner 不再直接接触 schema 列表
- Runner 不再直接接触工具函数表
- Runner 只负责“调度”

这就是更清晰的架构边界。

---

## 本节最值得注意的执行细节

### 无参 Tool

例如：

```python
get_current_time()
```

这类 Tool 的 `arguments` 可能是空对象。

### 有参 Tool

例如：

```python
calculator(expression)
```

这类 Tool 的 `arguments` 需要被正确解析并传给函数。

所以 `ToolManager.execute()` 的第一版就必须开始面对：

- 空参数调用
- 字典参数调用

这一步很重要，因为后面 `read_file(path)`、`search(query)` 都会建立在这个分发逻辑上。

---

## Code Review 视角

### 不推荐的写法

```python
class Runner:
    def run(...):
        ...
        tool_fn = self.tools[tool_name]
        result = tool_fn(...)
        ...
```

为什么不推荐？

因为这意味着 Runner 仍然保存和管理工具系统。

这样一来，Runner 就不只是运行器，还顺手承担了工具管理职责。

### 更推荐的写法

```python
class Runner:
    def run(...):
        ...
        result = tool_manager.execute(tool_name, arguments)
        ...
```

此时：

- Runner 只关心“调用工具”
- ToolManager 关心“如何找到并执行工具”

这才是更好的单一职责划分。

---

## 官方框架怎么做

成熟框架一般不会把 Tool 直接裸放在 Runner 里。

它们通常都会有一层更正式的工具系统，例如：

- Tool Registry
- Tool Manager
- Tool Context
- Tool Wrapper

即使名字不同，本质也都是在解决同一个问题：

> 让运行时调度器不必直接承担工具管理职责

所以这一节的内容其实非常接近真实框架源码里的核心思想。

---

## 本节最重要的一句话

> 当 Tool 数量开始增长时，真正需要的不是继续往 Runner 里塞逻辑，而是把 Tool 系统抽成独立模块。

这句话基本可以作为这一节的设计总结。

---

## 本节作业

### 任务 1

新增：

```python
class ToolManager:
    ...
```

### 任务 2

实现：

- `register_tool`
- `get_schemas`
- `execute`

### 任务 3

把已有 Tool 注册进去，例如：

- `get_current_time`
- `calculator`

### 任务 4

修改 Runner，让它通过 `ToolManager` 工作，而不是直接读字典或 schema 列表。

### 任务 5

让系统至少支持：

```text
现在几点？
18 * 29 等于多少？
```

并且确保新增 Tool 时尽量不需要修改 Runner。

---

## 本节 Git Commit

建议提交信息：

```text
Extract tool manager
```

---

## 下一步

下一节建议进入：

> Prompt 与 Message 组织

因为随着 ToolManager 抽出来后，Runner 的下一处复杂度会开始集中在：

- system prompt 怎么组织
- tool result 如何回填消息
- 多轮消息如何维护

也就是说，下一节会把项目进一步推进到：

> 更像真正的 Agent Runtime

