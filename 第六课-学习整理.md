# 第六课学习整理：真正理解 Responses API

## 本课定位

从这一课开始，不再停留在伪代码和流程图层面，而是正式进入现代 Agent 接口设计的核心认知。

这一课最重要的问题是：

> 为什么 OpenAI 推出了 `Responses API`，而不是继续只用 `Chat Completions`？

如果把这个问题想明白，就会真正开始理解现代 Agent 为什么会长成今天这样。

---

## 为什么教学方式要变化

前几课故意没有直接给出大段完整代码，是为了避免一种很常见但效果很差的学习方式：

> 复制几百行代码，跑通，但不理解。

从这一课开始，课程升级为一种更工程化的学习方式：

- 每一课只写 20 到 30 行左右代码
- 每一行都能解释清楚
- 每一层抽象都能还原到底层原理

这样长期来看，目标不只是“会写一个 Agent”，而是：

> 最终具备设计 Agent Framework 的能力。

---

## Chat Completions 的时代

过去常见的调用方式是：

```python
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {
            "role": "user",
            "content": "你好"
        }
    ]
)
```

它的核心输入结构是：

```text
messages
```

常见输出则是一个 assistant 消息。

这种模式非常适合：

- 聊天
- 问答
- 翻译
- 总结

因为它默认假设交互形态是：

```text
用户发消息
↓
模型返回文本
↓
结束
```

但 Agent 并不是这样工作的。

---

## Agent 真正需要的能力

Agent 需要的不是“一问一答”，而是一个持续交互过程：

```text
User
↓
LLM
↓
Tool Call
↓
Python
↓
Tool Result
↓
LLM
↓
继续 Tool
↓
LLM
↓
结束
```

在这个过程中，模型不仅要返回文本，还要能返回：

- 工具调用意图
- 中间推理相关结构
- 后续动作

并且系统还需要记住：

> 刚才调用了哪个 Tool，以及这个 Tool 返回了什么。

如果继续强行用传统聊天消息格式来承载这些复杂状态，会变得非常别扭。

所以 OpenAI 才推出了：

> `Responses API`

---

## Responses API 的核心思想

`Chat Completions` 更像是围绕“消息”设计的：

```text
message in
message out
```

而 `Responses API` 更像是围绕“响应对象”设计的：

```text
response in progress
response contains typed outputs
```

也就是说，模型返回的不再默认只是文本，而可能是多种类型的输出项。

可以把它理解成：

```text
Response

├── Text
├── Tool Call
├── Reasoning
├── Image
├── Audio
└── ...
```

这说明一个非常关键的变化：

> LLM 的输出不再只是“说一句话”，而是“发出一种事件”。

有时候这个事件是文本回答；

有时候这个事件是：

> 请先执行这个 Tool。

---

## 一个真实例子：天气查询

用户输入：

```text
北京天气怎么样？
```

在传统聊天思维下，我们倾向于期待模型直接返回：

```text
北京天气……
```

但在 Agent 语境下，更合理的流程可能是：

```text
Tool Call
↓
get_weather()
```

然后由程序执行 Tool，拿到结果：

```text
北京
32℃
晴
```

再把结果交回给模型，最终模型组织出自然语言：

> 北京今天晴，32℃。

这说明：

- 模型第一次输出未必是答案
- 第一次输出可能只是下一步动作指令

这正是 `Responses API` 更适合 Agent 的原因。

---

## Responses API 返回的不只是字符串

这是初学者非常容易忽略的一点。

很多人一拿到返回值就直接看：

```python
response.output_text
```

这在简单聊天场景里可能够用，但在 Agent 场景里通常不够。

因为一个完整的 `response` 对象通常不只有文本，还包括：

```text
response

├── output
├── output_text
├── usage
├── model
├── id
└── ...
```

其中对 Agent 来说，最关键的是：

```text
output
```

因为这里面可能出现的不是单一文本，而是不同类型的输出项，例如：

- `message`
- `function_call`
- 未来可能还包括其他动作类型

所以 Agent 开发者真正关心的，不是“有没有字符串”，而是：

> Response 里到底发生了什么事件。

---

## 第一个必须养成的习惯

以后拿到 `response`，第一反应不应该是：

```python
print(response.output_text)
```

而应该先看：

```python
print(response.output)
```

因为这能帮助你先判断当前这一轮返回的是：

- 普通消息
- Tool Call
- 其他结构化输出

这是 Agent 开发者和普通 LLM 应用开发者的一个重要区别。

普通开发者常常关注：

> 模型说了什么

而 Agent 开发者更先关注：

> 模型返回的是什么类型的事件

---

## 从文本驱动到事件驱动

这一课最重要的认知升级之一，是把程序思维从“文本驱动”切换为“事件驱动”。

普通 LLM 应用的运行方式更像：

```text
LLM
↓
文字
↓
结束
```

而 Agent 的运行方式更像：

```text
LLM
↓
判断 Response 类型
↓
如果是 Tool Call
↓
执行 Tool
↓
继续循环
↓
直到结束
```

这意味着：

> Agent 程序并不是围绕一段最终文本来写，而是围绕一系列“输出事件”来写。

这就是为什么很多 Agent SDK 的底层实现，都会有类似这样的逻辑：

```python
for item in response.output:
    ...
```

本质上，它是在遍历模型在这一轮里发出的所有事件。

---

## 为什么很多人学不会 Agent

一个很常见的问题是，很多人始终停留在这样的使用方式：

```python
print(response.output_text)
```

这对聊天机器人没有问题，但对 Agent 来说会错过最重要的信息：

- 有没有 Tool Call
- 有没有结构化动作
- 有没有多种输出并存

因此他们写出来的程序虽然调用了新接口，但思维仍然停留在老模式里。

真正的 Agent 代码更关心的是：

> `response.output` 里有哪些 item，它们分别是什么 type

只要这一点理解透了，后面看任何 Agent SDK 的设计都会顺很多。

---

## 本课最重要的一道思考题

两种写法：

### 方式 A

```python
print(response.output_text)
```

### 方式 B

```python
for item in response.output:
    print(item.type)
```

为什么普通聊天机器人通常只需要方式 A，而真正的 Agent 必须采用方式 B？

核心答案是：

- 普通聊天机器人只关心最后生成的文本
- Agent 需要先判断当前返回的是“什么类型的事件”，再决定下一步程序动作

也就是说：

> 聊天机器人消费的是文本结果，Agent 消费的是结构化事件流。

---

## 本课核心结论

### 1. Chat Completions 更适合消息式对话

它天然面向“输入消息，输出文本”。

### 2. Responses API 更适合 Agent

因为 Agent 需要处理的不只是文本，还包括 Tool Call 等多种输出类型。

### 3. Agent 开发者首先要看 `response.output`

而不是只盯着 `response.output_text`。

### 4. 现代 Agent 本质上是事件驱动系统

程序要根据返回的不同事件类型决定下一步动作。

### 5. `for item in response.output` 是非常典型的 Agent 思维

它体现了对结构化输出的遍历与分派，而不是只读取一段最终字符串。

---

## 下一课预告

下一课将开始写第一段真正的 Responses API 代码，主要内容包括：

1. 初始化 `OpenAI` Client
2. 调用 `responses.create()`
3. 打印完整的 `response.output`
4. 观察返回结构
5. 学会区分 `message` 和 `function_call`

从那一课开始，就会正式把“事件驱动的 Agent 思维”落到代码层面。

