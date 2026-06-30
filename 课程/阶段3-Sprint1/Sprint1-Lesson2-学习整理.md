# Sprint 1 - Lesson 2 学习整理

## 本节定位

这一节开始，`agent-from-scratch` 项目第一次真正打通了最小调用链路：

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

这意味着项目第一次从“只有架构骨架”进入“可以真正调模型”的阶段。

---

## 本节目标

本节只做一件事：

> 让 Runner 真正通过统一的 LLM 抽象层去调用 Responses API，并打印 `response.output_text`

这一节刻意不接 Tool，是为了先把最基础、最稳定的一条链路打通。

---

## 本节核心知识点

### 1. BaseLLM 是统一接口

本节先定义：

```python
class BaseLLM(ABC):
    @abstractmethod
    def generate(self, messages, tools=None):
        ...
```

它的意义不是多写一层代码，而是建立统一模型接口。

以后无论底层是：

- OpenAI
- Claude
- Gemini
- Qwen

上层 Runner 和 Agent 只依赖：

```python
generate()
```

这就是多态，也是依赖倒置在项目里的直接体现。

### 2. OpenAILLM 是具体实现

在 `BaseLLM` 之下，再实现：

```python
class OpenAILLM(BaseLLM):
    ...
```

这样就把“模型接口”和“模型供应商实现”分开了。

### 3. Agent 从保存 `model` 升级为保存 `llm`

这是本节很重要的一次架构升级。

之前：

```python
Agent(model="gpt-5", ...)
```

现在：

```python
Agent(llm=OpenAILLM(...), ...)
```

这意味着 Agent 不再依赖一个字符串模型名，而是依赖一个真正的 LLM 能力对象。

---

## 本节代码成果

由于当前环境对已有文件的直接更新有限制，这一节采用了并行落地方式，新增了：

- `agent_lesson2.py`
- `llm_lesson2.py`
- `runner_lesson2.py`
- `app_lesson2.py`

它们完整表达了本节应该有的代码结构，后续环境允许时可以再合并回主文件名。

### `llm_lesson2.py`

新增了：

- `BaseLLM`
- `OpenAILLM`

其中 `OpenAILLM.generate()` 内部调用：

```python
client.responses.create(...)
```

### `agent_lesson2.py`

把 Agent 设计为保存 `llm / instructions / tools` 的配置对象。

### `runner_lesson2.py`

`Runner.run()` 现在会真正：

1. 组装 `messages`
2. 调用 `agent.llm.generate(...)`
3. 打印 `response.output_text`

### `app_lesson2.py`

首次把整个链路真正串起来：

```python
llm = OpenAILLM()
agent = Agent(...)
runner = Runner()
runner.run(...)
```

---

## Code Review 视角

### 为什么不能这样写

```python
class Agent:
    def run(self):
        response = OpenAI().responses.create(...)
```

因为这会让 Agent 直接依赖 OpenAI SDK，造成高耦合。

一旦未来要换：

- Claude
- Gemini
- Qwen

整个 Agent 都要改。

### 为什么现在的设计更好

因为现在的依赖关系是：

```text
Agent
  ↓
BaseLLM
  ↓
OpenAILLM
  ↓
Responses API
```

这样：

- Agent 只知道 LLM 接口
- OpenAILLM 才知道 OpenAI 细节

这就是典型的低耦合设计。

---

## 本节最值得记住的一句话

> Agent 不应该知道 OpenAI，它只应该知道 LLM Interface。

这句话几乎决定了后面整个项目的可扩展性。

---

## 本节 Git Commit

建议提交信息：

```text
Add OpenAI LLM wrapper
```

这个 Commit 的意义是：

> 项目第一次真正具备了调模型能力。

---

## 下一步

下一节将进入整个课程最关键的一步：

```python
while True:
    response = llm.generate(...)

    if response 是 Tool Call:
        执行 Tool
        把结果发回 LLM
    else:
        return 最终答案
```

也就是说，下一节会从“能调模型”升级到“真正的最小 Agent Loop”。

