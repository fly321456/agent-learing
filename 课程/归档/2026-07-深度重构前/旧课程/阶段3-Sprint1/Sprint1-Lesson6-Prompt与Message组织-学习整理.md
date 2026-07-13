# Sprint 1 - Lesson 6 学习整理

## 本节定位

前面几节课，我们已经逐步搭起了最小 Agent 的核心骨架：

- `Agent`：保存配置
- `Runner`：驱动运行
- `BaseLLM / OpenAILLM`：统一模型接口
- `ToolManager`：管理 Tool
- `Agent Loop`：最小闭环

但到目前为止，还有一个很容易被低估、却会直接决定后续系统稳定性的模块：

> Prompt 与 Message 组织

很多初学者会把消息列表当成“随便拼接的字符串容器”，但对于 Agent 来说，消息组织本身就是运行时设计的一部分。

所以这一节的重点是：

> 让 Runner 不只是“会循环”，还要“会正确组织上下文”。

---

## 本节目标

把当前系统的消息组织方式，从“临时拼几个字典”升级成一套更清晰、更稳定的最小约定。

这一节希望明确三件事：

1. `system prompt` 应该放哪
2. `user input` 应该如何进入上下文
3. `tool result` 应该如何回填给 LLM

最终要形成一条更完整的消息链路：

```text
system instructions
↓
user message
↓
LLM response
↓
tool call
↓
tool result message
↓
LLM final answer
```

这一步做对了，后面加入 Session、Memory、多轮对话时会轻松很多。

---

## 本节核心知识点

### 1. Prompt 不是一段装饰性文字，而是系统行为边界

很多人刚开始写 Agent 时，会把 Prompt 理解成：

```text
你是一个助手。
```

然后随手塞进代码里。

这在最初可以工作，但很快会出现几个问题：

- Prompt 内容越来越长
- Prompt 与业务逻辑混在一起
- 难以复用
- 难以调试“到底是 Prompt 问题还是代码问题”

所以从工程视角看：

> Prompt 是系统配置的一部分，不是临时字符串。

这也是为什么后面很多框架都会把 Prompt 单独抽出来。

---

### 2. Message 列表不是普通数组，而是运行时上下文

很多初学者第一次接触 `messages` 时，会觉得它只是：

```python
[
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."},
]
```

但在 Agent 里，这个列表的真正意义是：

> 当前运行时上下文

也就是说，它不只是“消息历史”，而是 LLM 做决策时唯一能看到的世界。

因此消息怎么组织，直接决定：

- 模型能不能理解任务
- 模型能不能正确选择 Tool
- 模型能不能基于 Tool Result 继续推理

所以后面为什么会引入 `Session`，本质上就是为了把这份上下文管理好。

---

### 3. Tool Result 回填不是随便 append 一条字符串

这一点非常关键。

很多初学者第一次做 Tool Loop，会这样写：

```python
messages.append({
    "role": "user",
    "content": f"tool result: {result}"
})
```

看起来能跑，但这是一种非常脆弱的做法。

原因是：

- 它混淆了用户输入和工具返回
- 它没有表达“这是一次工具执行结果”
- 模型未必能稳定理解当前上下文结构

所以这一节最重要的工程意识之一是：

> Tool Result 应该作为一种结构化上下文被回填，而不是伪装成普通用户消息。

在最小项目阶段，即使我们先用简单消息格式模拟，也要明确知道：

- 这只是过渡实现
- 后续会升级为更明确的 Tool Result 结构

---

## 本节推荐的最小设计

这一节不追求一步做成完整 Session 系统，而是先建立最小但正确的约定。

### 约定 1：由 Agent 提供 `instructions`

```python
agent.instructions
```

### 约定 2：Runner 每次运行时总是先构造 system message

```python
{"role": "system", "content": agent.instructions}
```

### 约定 3：用户输入永远作为 user message 进入

```python
{"role": "user", "content": user_input}
```

### 约定 4：Tool Result 回填时，至少要明确说明它来自哪个 Tool

例如：

```python
{
    "role": "system",
    "content": "Tool get_current_time returned: 2026-06-30 21:30:00"
}
```

注意：

这不一定是未来最终形态，但它比“伪装成用户输入”要更清晰。

---

## 为什么这一步不能跳过

很多人会觉得：

> 先能跑就行，消息怎么拼以后再说。

但现实里，消息组织一旦混乱，后面最容易出现的现象是：

- Tool Call 时好时坏
- 模型明明拿到 Tool Result 却继续重复调用
- 模型忘记当前任务目标
- 同样代码不同 prompt 结果差异巨大

这类问题最后通常都很难 debug。

因为它们表面上像“模型不稳定”，本质上往往是：

> 运行时上下文组织得不够清晰

所以这一步必须尽早建立规则。

---

## 本节建议的代码边界

这一节最适合开始把消息组织逻辑从 `Runner.run()` 里稍微抽出来一点。

例如，Runner 至少可以有这样的辅助方法：

### `_build_initial_messages`

负责生成：

- system message
- user message

### `_append_tool_result`

负责把 Tool 结果回填回上下文

这样做的好处是：

- `run()` 主流程更清晰
- 消息组织逻辑可单独调整
- 为后续 `Session` 抽象做准备

注意：

> 这一节还不是要正式上 Session，而是先为 Session 铺路

---

## 一个建议的最小流程

### Step 1：初始化消息

```python
messages = [
    {"role": "system", "content": agent.instructions},
    {"role": "user", "content": user_input},
]
```

### Step 2：调用 LLM

```python
response = llm.generate(messages, tools=tool_manager.get_schemas())
```

### Step 3：如果有 Tool Call，就执行 Tool

```python
result = tool_manager.execute(tool_name, arguments)
```

### Step 4：把 Tool Result 回填进 messages

```python
messages.append(...)
```

### Step 5：继续调用 LLM

直到没有 Tool Call，返回最终答案。

这个流程表面上看和上一节一样，但这节关注的是：

> 每一步消息是怎么组织进上下文的

---

## Code Review 视角

### 不推荐的写法

```python
messages = []
messages.append({"role": "user", "content": user_input})
...
messages.append({"role": "user", "content": str(result)})
```

问题在于：

- 没有 system instructions
- Tool Result 混成普通 user message
- 上下文结构非常模糊

这会让模型很难稳定理解当前状态。

### 更推荐的写法

```python
messages = self._build_initial_messages(agent, user_input)
...
messages = self._append_tool_result(messages, tool_name, result)
```

这样虽然还是最小实现，但已经开始具备：

- 上下文边界
- 消息职责分层
- 未来可抽象性

---

## 官方框架怎么做

成熟框架一般不会让消息组织逻辑完全散落在主循环里。

它们通常会通过这些方式管理上下文：

- `Session`
- `Message Store`
- `Conversation State`
- `Run Context`

名字不同，但本质都一样：

> 把“消息历史 + 当前运行状态”作为一等公民管理起来

所以这一节其实就是在为后续的 `Session` 抽象打地基。

---

## 本节最重要的一句话

> Agent 的上下文不是“拼接出来的文本”，而是“被组织起来的运行时状态”。

这句话非常重要。

因为它决定了你以后是把 Prompt / Message 当作临时变量，还是把它们当作系统运行时的一部分。

---

## 本节作业

### 任务 1

把 `system prompt` 的构造固定下来，不要再临时拼。

### 任务 2

把 `user input` 的消息组织与 `tool result` 的消息组织区分开。

### 任务 3

在 Runner 里新增辅助方法，例如：

- `_build_initial_messages`
- `_append_tool_result`

### 任务 4

确保以下场景都能稳定工作：

```text
现在几点？
18 * 29 等于多少？
```

并检查 Tool Result 回填后，模型是否能基于结果生成最终自然语言答案。

---

## 本节 Git Commit

建议提交信息：

```text
Refine prompt and message flow
```

---

## 下一步

下一节最自然的升级方向是：

> 引入 `Session` 初版

因为一旦消息组织逻辑开始稳定，下一步就应该把：

- 当前消息列表
- 当前轮次状态
- 后续多轮对话能力

收拢成一个正式的运行时对象。

