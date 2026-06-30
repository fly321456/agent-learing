# Sprint 1 - Lesson 7 学习整理

## 本节定位

前面几节课，我们已经把最小 Agent 的几个关键骨架搭起来了：

- `Agent`
- `Runner`
- `BaseLLM / OpenAILLM`
- `ToolManager`
- `Prompt / Message` 组织
- 最小 Agent Loop

但到目前为止，还有一个非常明显的问题：

> `messages` 仍然只是 Runner 里的一个临时变量

这在最小 demo 里可以工作，但一旦系统要支持：

- 多轮对话
- 多次 Tool Call
- 中间状态查看
- 后续 Memory

它就会很快失控。

所以这一节的核心目标非常明确：

> 把“临时消息列表”升级成“Session 初版”

这一步一旦做对，项目就会第一次真正具备：

> 运行时状态对象

---

## 本节目标

把当前 Agent 的上下文管理，从：

```python
messages = [...]
```

升级为：

```python
session = Session(...)
```

并让 Runner 不再直接手写管理消息列表，而是通过 Session 来完成：

- 初始化上下文
- 追加用户消息
- 追加 Tool Result
- 读取完整消息历史

最终目标是形成这样的链路：

```text
User
  │
  ▼
Runner
  │
  ▼
Session
  │
  ▼
LLM
  │
  ▼
ToolManager
  │
  ▼
Session
  │
  ▼
LLM
```

这一节学完后，项目就会从“能跑的 Agent”进一步升级成“开始有运行时状态管理能力的 Agent”。

---

## 本节核心知识点

### 1. 为什么 `messages` 不能一直只是局部变量

当前最小版本里，很多实现会把上下文直接写在 `Runner.run()` 里：

```python
messages = [
    {"role": "system", "content": agent.instructions},
    {"role": "user", "content": user_input},
]
```

然后在循环里不断：

```python
messages.append(...)
```

这在最初没有问题，但它会立刻带来几个工程问题：

- 上下文管理逻辑和 Runner 主流程混在一起
- 追加消息、读取消息、调试消息没有边界
- 后续加入多轮对话会很难收敛
- Memory 根本没有接入位置

所以真正的问题不是“列表能不能用”，而是：

> 运行时状态不能长期裸露在主流程里

---

### 2. Session 的本质是什么

很多人第一次听到 `Session`，会把它理解成“聊天记录”。

这不完全错，但不够准确。

更准确的理解应该是：

> Session 是当前 Agent 运行过程中的上下文容器

它至少应该负责：

- 保存当前消息历史
- 提供消息追加接口
- 提供读取完整上下文的接口

换句话说，Session 不是简单的 list 包装，而是：

> Agent Runtime 的最小状态对象

这就是为什么成熟框架里几乎一定会出现 Session、Conversation、RunContext 之类的抽象。

---

### 3. 为什么 Session 属于运行时层，不属于 Agent

这一步特别重要。

`Agent` 负责的是静态配置：

- 我是谁
- 我用哪个 LLM
- 我有哪些 Tool
- 我的 Prompt 是什么

而 `Session` 管的是动态状态：

- 当前有哪些消息
- 当前执行到了哪一轮
- Tool Result 回填到了哪里

所以：

- `Agent` 属于配置层
- `Session` 属于运行时层

这也是为什么 Session 应该由 Runner 驱动使用，而不是塞回 Agent 里。

---

## 本节推荐的最小 Session 设计

这一节不需要一上来做得很重。

最小正确版本足够是一个类，例如：

```python
class Session:
    def __init__(self, instructions):
        ...
```

它内部可以先保存：

- `messages`

并提供几个最小方法：

### `add_user_message`

负责追加用户输入。

### `add_tool_result`

负责回填 Tool 执行结果。

### `get_messages`

负责把当前完整上下文交给 LLM。

### 可选：`reset`

负责重置会话。

这一版先不追求长期记忆、持久化、并发会话等能力。

这一节只做：

> 把 Session 作为上下文管理边界正式建立起来

---

## 本节 Runner 会发生什么变化

上一节的 Runner 可能还是这种感觉：

```python
messages = self._build_initial_messages(...)
...
messages = self._append_tool_result(...)
```

这一节之后，Runner 更合理的方向应该是：

```python
session = Session(agent.instructions)
session.add_user_message(user_input)

while True:
    response = llm.generate(session.get_messages(), ...)
    ...
    session.add_tool_result(tool_name, result)
```

这个变化看起来不大，但意义非常大。

因为它意味着：

- `messages` 不再裸露在主流程里
- 上下文进入了独立运行时对象
- Runner 逻辑开始真正“像调度器”

这就是一个非常明确的架构升级。

---

## 本节一个容易忽略但非常关键的点

Session 的第一版虽然简单，但它已经决定了后续很多能力的接入位置。

例如未来你要加：

- 多轮用户对话
- 历史截断
- Token 裁剪
- Memory 检索结果注入
- Checkpoint 恢复

这些几乎都会落在 Session 周边。

所以这一节不是“小封装”，而是：

> 给后续几乎所有运行时增强能力提前预留接口位置

---

## Code Review 视角

### 不推荐的写法

```python
class Runner:
    def run(...):
        messages = []
        messages.append(...)
        messages.append(...)
        messages.append(...)
```

问题在于：

- Runner 同时做流程控制和上下文管理
- 未来每加一种消息类型，Runner 就会继续膨胀
- 很难复用会话逻辑

### 更推荐的写法

```python
class Session:
    ...

class Runner:
    def run(...):
        session = Session(...)
        ...
        response = llm.generate(session.get_messages(), ...)
```

这样：

- Session 管状态
- Runner 管流程

这就符合前面一直强调的：

> 高内聚、低耦合

---

## 官方框架怎么做

成熟框架很少会长期让 `messages` 以裸 list 的形式散在主循环里。

它们通常都会引入某种运行时上下文对象，例如：

- `Session`
- `Conversation`
- `RunContext`
- `State`

名字不同，但本质类似：

> 把“当前消息历史 + 当前运行状态”正式收进一个对象里

这也是为什么前面我们一直说：

> Agent Framework 的核心不是类名，而是运行时边界划分

Session 就是其中非常关键的一条边界。

---

## 本节最重要的一句话

> 当上下文开始影响系统行为时，它就不应该继续只是局部变量，而应该升级为运行时对象。

这句话就是这一节的设计核心。

---

## 本节作业

### 任务 1

新增：

```python
class Session:
    ...
```

### 任务 2

至少实现这些方法：

- `add_user_message`
- `add_tool_result`
- `get_messages`

### 任务 3

修改 Runner，让它不再直接维护 `messages` 列表，而是改为通过 `Session` 工作。

### 任务 4

确保以下场景仍然能跑通：

```text
现在几点？
18 * 29 等于多少？
```

并观察：Tool Result 回填后，LLM 是否还能正常生成最终答案。

---

## 本节 Git Commit

建议提交信息：

```text
Add session abstraction
```

---

## 下一步

下一节最自然的推进方向是：

> 最小测试

因为从这一节开始，系统已经不再只是几个函数，而是开始出现：

- `Runner`
- `ToolManager`
- `Session`

一旦这些运行时对象都出现了，测试就必须尽快跟上。

