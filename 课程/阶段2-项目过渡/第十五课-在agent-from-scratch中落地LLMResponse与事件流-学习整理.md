# 第十五课学习整理：在 agent-from-scratch 中落地 LLMResponse 与事件流

## 本课定位

第十三课我们解决的是：

> 为什么 Agent 的输出不能长期停留在纯文本

第十四课我们进一步解决的是：

> 统一响应协议应该长什么样，`LLMResponse / ToolCall / Event / Block` 为什么值得被抽象出来

但到这里，课程还差最后一块非常关键的拼图：

> 这套协议什么时候真正进入项目代码，而不只是停留在设计层？

所以第十五课的任务非常明确：

> 把第十四课的协议设计，正式接到 `agent-from-scratch` 的实现主线上

也就是说，这一课不是再讲新概念，而是一节非常典型的“桥接课”：

> 从协议设计，走向代码落地

---

## 为什么这节课必须单独存在

如果没有这一课，当前课程会出现一个很微妙但真实存在的断层。

因为现在的链路是这样的：

- 第十课：理解 `LLM Interface`
- 第十一课：理解 OpenAI Agents SDK 的分层
- 第十二课：自己写出最小 Agent
- 第十三课：意识到输出必须结构化
- 第十四课：设计统一响应协议

但问题是：

> 第十四课已经把协议讲完了，可项目代码还没有一个明确的“接入时刻”

而我们刚刚重写过的 `Sprint1-Lesson1` 又明确强调：

> 这一节先立骨架，不急着把 `LLMResponse` 一口气实现进去

这就意味着：

- 第十四课已经完成“设计层闭环”
- Sprint1-Lesson1 只完成“骨架层起步”
- 中间还缺一个“协议如何进代码”的专门桥梁

这就是第十五课应该存在的理由。

---

## 这节课真正要回答的不是“要不要做”，而是“从哪里开始做”

很多同学到这里其实已经接受一个事实：

> `return response.output_text` 迟早要升级

真正困难的地方不在认知上，而在实现顺序上。

比如你很容易马上遇到这些问题：

- 先改 `llm.py` 还是先改 `runner.py`
- `LLMResponse` 是不是要一步到位
- Tool 调用结果是不是现在就抽象成 `ToolCall`
- 事件流是不是要等 Tracing 再做
- `blocks` 没前端时是不是可以先空着

所以这一课的核心不是继续证明“结构化输出很重要”，而是：

> 给出一条最小、稳定、不会过度设计的落地路径

---

## 第十五课和 Sprint1 的关系

这节课虽然放在阶段 2，但它本质上已经开始为 Sprint1 铺路。

因为它不是再增加一个独立知识点，而是在回答：

> Sprint1 后面的实现，应该以什么样的输出对象为中心继续长

也就是说：

### 阶段2前半段解决

- 为什么做自己的 Agent
- 为什么抽象 LLM
- 为什么理解官方框架
- 为什么先写最小闭环

### 阶段2后半段解决

- 为什么输出要结构化
- 协议应该如何设计
- 协议应该如何进入代码

这意味着第十五课其实是：

> 阶段2通往阶段3的最后一块踏板

---

## 从这一课开始，`response.output_text` 应该被视为“过渡方案”

在最小 Agent 阶段，直接打印：

```python
response.output_text
```

是完全合理的。

因为那时目标只有一个：

> 先把调用链跑通

但到了现在，如果仍然把它当作长期主输出，就会开始出现问题。

因为它会让：

- Runner 只能处理文本
- Tool 结果只能隐含在文本里
- 过程事件无法成为正式输出
- 前端未来只能消费自然语言
- 测试很难断言结构化语义

所以从这一课开始，一个很重要的观念应该正式建立起来：

> `response.output_text` 不是错误，但它应该被视为过渡方案，而不是终局结构

---

## 最合理的落地顺序：先改 `llm.py`，再改 `runner.py`

如果要把协议正式接进项目，最稳妥的顺序通常不是到处同时改，而是按边界推进。

最推荐的顺序是：

### 第一步：先改 `llm.py`

先让 `llm.py` 的输出从：

```python
return response.output_text
```

升级为：

```python
return LLMResponse(...)
```

原因很简单：

> `llm.py` 本来就是模型输出进入系统的第一道边界

如果这一层还在返回裸文本，那么后面其他层都只能继续围绕裸文本工作。

### 第二步：再改 `runner.py`

等 `llm.py` 能稳定返回 `LLMResponse` 之后，`Runner` 才有机会开始处理：

- `content`
- `tool_calls`
- `events`
- `finish_reason`

也就是说：

> 先让结果对象存在，再让运行时学会消费它

这个顺序比同时改多层更稳。

---

## 第一版 `LLMResponse` 不要一步到位做复杂

这节课特别要防止一个新的误区：

> 既然协议都要落地了，那是不是应该把完整类型系统一次性做出来？

不建议。

第一版最合理的做法是：

> 用最小结构先把主干打通

例如：

```python
class LLMResponse:
    def __init__(
        self,
        content: str = "",
        tool_calls: list | None = None,
        events: list | None = None,
        blocks: list | None = None,
        finish_reason: str | None = None,
        raw_response: object | None = None,
    ):
        self.content = content
        self.tool_calls = tool_calls or []
        self.events = events or []
        self.blocks = blocks or []
        self.finish_reason = finish_reason
        self.raw_response = raw_response
```

这里最重要的不是“写得多漂亮”，而是：

- 上层终于不再只依赖字符串
- 结果对象终于有统一入口
- 后面字段增强有位置可长

这就够了。

---

## 为什么第一版 `ToolCall / Event / Block` 应该尽量轻

很多时候，系统第一次落地协议失败，不是因为抽象错了，而是因为抽象太重了。

比如一上来就：

- 定义十几种 Tool 状态
- 定义二十几种 Event 类型
- 设计很强的 Block 类型树

这样会让实现成本暴涨，而且真实项目往往还没积累足够多的使用反馈。

所以第十五课更合理的建议是：

### `ToolCall`

先只关心：

- `name`
- `arguments`
- `status`
- `summary`

### `Event`

先只关心：

- `type`
- `text`
- `name`
- `data`

### `Block`

先只关心：

- `type`
- `data`

这就足够支撑：

- 基础调试
- 基础工作台
- 协议演进

不要一开始就把“未来可能需要的复杂性”全预埋进去。

---

## `Runner` 在这一步会发生什么变化

一旦 `llm.py` 改为返回 `LLMResponse`，`Runner` 的职责会发生一个非常关键的升级。

过去的 `Runner` 更像：

```python
response = llm.generate(...)
print(response)
```

而往后它会逐步变成：

```python
response = llm.generate(...)

consume(response.content)
observe(response.events)
route_tool_calls(response.tool_calls)
```

也就是说，`Runner` 从“文本搬运器”开始变成真正的：

> 运行时结果协调器

这一步很关键，因为它意味着：

- Tool Calling 不再只是模型内部现象
- 过程事件不再只是日志副产品
- 输出对象开始真正进入系统运行时

---

## 为什么 `blocks` 现在可以先存在但暂时不激活

很多同学会担心：

> 现在项目里还没有前端，那 `blocks` 这个字段是不是没必要先放进去？

更合理的答案是：

> 可以先存在，但不必强求现在就大量生产它

原因是：

- `blocks` 属于未来明确会增长的结构化结果位
- 现在不一定马上用，但以后几乎一定会用
- 先把位置留出来，远比以后再临时加进去更稳

所以当前阶段可以采用这种策略：

- `content` 立即投入使用
- `tool_calls` 开始投入使用
- `events` 开始投入使用
- `blocks` 先预留字段，必要时只返回空数组

这是一种很典型的“边界先行、能力渐进”的工程手法。

---

## 这节课对 `agent-from-scratch` 的直接影响

如果把第十五课真正落到项目里，`agent-from-scratch` 后续会发生非常实在的变化。

### 1. `llm.py` 不再只负责“拿到文本”

而是负责：

> 把底层模型输出整理成系统级响应对象

### 2. `runner.py` 不再只负责“打印结果”

而是开始负责：

> 消费系统级响应对象

### 3. Tool 调用链会更容易继续长

因为调用结果终于不再只是隐含在自然语言里。

### 4. 未来接前端时不会推倒重来

因为输出协议已经开始向：

- `content`
- `events`
- `blocks`

这种结构靠拢。

### 5. 测试会变得更自然

因为你可以开始断言：

- `response.tool_calls`
- `response.events`
- `response.finish_reason`

而不只是断言某段文本里是否“看起来像包含了这些信息”。

---

## 第十五课完成后，系统应该达到什么状态

这节课完成后，最理想的状态不是“所有能力都实现了”，而是下面这件事成立了：

> 项目的输出主干，已经从字符串正式切换到了响应对象

也就是说，项目应该至少具备这些信号：

- `llm.py` 返回 `LLMResponse`
- `Runner` 开始面向 `LLMResponse` 编程
- `ToolCall / Event / Block` 至少有最小占位结构
- `response.output_text` 不再是唯一结果通道

只要这四件事成立，后面继续往：

- Tool Calling
- Event 流
- 工作台
- 测试
- Tracing

这些方向演进都会顺很多。

---

## 这节课最容易踩的误区

### 误区 1：把它理解成“只是改个返回值”

它表面上像是改返回值，实际上是在改系统输出边界。

### 误区 2：以为必须一口气把完整协议全部做完

不是。

这节课更强调：

> 先把主干切过去，再逐步增强细节

### 误区 3：因为没有前端，就先不考虑 `events / blocks`

这会让你以后再补协议时重新返工。

更稳的做法是：

> 先留边界，再慢慢启用能力

---

## 本课核心结论

### 1. 第十五课是一节桥接课，不是概念扩展课

它负责把第十四课的协议设计正式接到项目代码里。

### 2. 最合理的落地顺序是先改 `llm.py`，再改 `runner.py`

先让响应对象存在，再让运行时消费它。

### 3. 第一版 `LLMResponse` 应该追求最小可用，而不是一步到位的复杂类型系统

这更符合当前阶段的工程节奏。

### 4. `ToolCall / Event / Block` 第一版应尽量轻

先承载稳定语义，再慢慢增强细节。

### 5. 从这一课开始，`response.output_text` 应该被视为过渡方案，而不是长期结构

真正长期稳定的，是系统级响应对象。

---

## 下一步

这节课之后，最自然的推进方向已经非常清楚：

- 在 `agent-from-scratch` 里真正创建 `LLMResponse`
- 让 `llm.py` 返回 `LLMResponse`
- 让 `Runner` 消费 `LLMResponse`
- 再继续推进 Tool Calling 闭环和事件流输出

也就是说，接下来真正开始发生的，是：

> 从“项目能调模型”进入“项目开始拥有自己的输出协议”
