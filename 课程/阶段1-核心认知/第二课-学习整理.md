# 第二课学习整理：LLM 是怎么知道调用哪个 Tool 的？

## 本课核心问题

如果我们给模型一个工具：

```python
def get_weather(city):
    ...
```

当用户问：

```text
上海今天天气怎么样？
```

为什么 LLM 会知道应该调用 `get_weather()`？

这节课要建立的核心认知是：

> LLM 不执行 Tool，它只负责决定调用哪个 Tool；真正执行 Tool 的，是外部程序。

---

## Agent 中 Tool Calling 的真实过程

很多初学者想象中的流程是：

```text
用户
↓
LLM
↓
Python 运行
↓
返回
```

但真实流程更接近：

```text
用户
↓
LLM
↓
"建议调用某个 Tool"
↓
程序执行 Tool
↓
Tool 结果返回给 LLM
↓
LLM 组织最终回答
```

重点在于：

> 真正执行 Tool 的不是 LLM，而是你的程序。

---

## 最简单的例子：加法 Tool

假设定义了一个函数：

```python
def add(a, b):
    return a + b
```

用户问：

```text
15 + 28 等于多少？
```

很多人以为模型会直接执行：

```python
add(15, 28)
```

实际上不是。

LLM 更可能输出一段结构化信息，例如：

```json
{
  "tool": "add",
  "arguments": {
    "a": 15,
    "b": 28
  }
}
```

它表达的含义是：

> 我建议调用 `add` 这个 Tool，并传入这些参数。

然后由外部程序真正执行：

```python
result = add(15, 28)
```

得到结果：

```text
43
```

再把结果返回给 LLM，LLM 才能生成最终自然语言答案：

```text
15 + 28 = 43
```

---

## Tool Calling 的本质

一句话总结：

> Tool Calling 的本质，就是 LLM 输出一段结构化的调用意图。

这段结构化内容通常可以理解为 JSON，例如：

```json
{
  "tool": "weather",
  "city": "北京"
}
```

或者：

```json
{
  "tool": "search",
  "keyword": "Agent Development"
}
```

严格来说，不同平台底层格式可能不是“原始 JSON 字符串”，但在理解层面上，把它看成：

> 一段描述“该调用哪个工具、传什么参数”的结构化数据

是非常准确的。

---

## 为什么 LLM 知道该调用哪个 Tool

原因不是它真的会执行代码，而是：

> 我们提前把 Tool 的说明书告诉了它。

例如给模型的 Tool 定义可能包含：

```text
Tool Name:
get_weather

Description:
查询某个城市天气

Parameters:
city: string
```

当模型看到用户输入：

```text
上海天气
```

它就会根据工具说明判断：

> 这个需求和 `get_weather` 的描述匹配。

于是输出对应的 Tool Call。

所以模型的能力不是“会执行函数”，而是：

> 会把用户意图映射到最合适的工具定义。

---

## Tool 的四个核心组成部分

以后设计 Tool，通常都可以拆成四部分：

```text
Tool
├── Name
├── Description
├── Parameters
└── Function
```

### 1. Name

工具名称，供模型识别和调用。

例如：

```text
read_file
browser_search
get_weather
```

### 2. Description

工具说明，告诉模型这个工具是干什么的、适用于什么场景。

### 3. Parameters

工具入参，也就是模型调用该工具时必须提供哪些字段。

例如：

```text
path
city
keyword
```

### 4. Function

真正执行逻辑的程序代码。

例如：

```python
open(path)
```

或者：

```python
requests.get(...)
```

---

## 一个真实 Tool 的样子

以天气工具为例：

### Name

```text
get_weather
```

### Description

```text
查询指定城市天气
```

### Parameters

```text
city
```

### Return

```json
{
  "temperature": 30,
  "weather": "Sunny"
}
```

当用户说：

```text
广州天气？
```

模型就可能输出：

```json
{
  "tool": "get_weather",
  "arguments": {
    "city": "广州"
  }
}
```

---

## 为什么 Description 比代码还重要

很多新人会写：

```python
def weather():
    ...
```

但是不给描述，或者描述非常模糊。

这样模型往往不知道这个函数适合用在什么场景。

更好的 Description 应该像这样：

```text
查询指定城市实时天气。
适用于天气、温度、降雨、空气质量等相关问题。
```

结论是：

> Description 越清楚，模型越容易做出正确的工具选择。

所以在 Agent 开发里，经常会出现一个反直觉现象：

> Tool 的描述质量，往往比函数实现本身更影响调用效果。

---

## 一个现代 Agent 的基础运行流程

```text
定义 Tool
↓
告诉 LLM 有哪些 Tool
↓
用户输入
↓
LLM 决定调用哪个 Tool
↓
程序执行 Tool
↓
Tool Result
↓
LLM 继续思考
↓
结束
```

这里再次可以看出：

- Tool 本身不是最复杂的部分
- 真正复杂的是循环决策与上下文管理

也就是后续要深入的 `Loop`

---

## 本课最重要的一句话

> LLM 不执行 Tool，它只决定调用哪个 Tool；真正执行 Tool 的，是你的程序。

这是进入 Agent 开发之后必须牢牢记住的底层认知。

---

## 下一步学习方向

下一课开始，将进入不依赖框架的最小 Agent 实现，整体结构是：

```text
User
   │
   ▼
Python 程序
   │
   ▼
LLM
   │
   ├── 普通回答
   │
   └── Tool Call
           │
           ▼
      Python 执行 Tool
           │
           ▼
      Tool Result
           │
           ▼
        LLM 总结
           │
           ▼
        Final Answer
```

目标是在约 100 到 150 行 Python 内，亲手实现一个最小可运行 Agent。

