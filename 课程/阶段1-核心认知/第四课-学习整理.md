# 第四课学习整理：从 0 编写第一个 Agent

## 本课定位

从这一课开始，正式进入第一个 Agent 的实际开发阶段。

但这节课依然没有直接上完整代码，而是先做两件更重要的事：

- 搭建开发环境
- 建立最小 Agent 的实现认知

本课的教学方式强调：

> 不只是知道代码怎么写，更要知道为什么这样写。

因为 Agent 开发和普通 Python 编程最大的区别，不在于语法，而在于设计思想。

---

## 本课目标

本课的目标不是一次性写完完整 Agent，而是完成第一版 Agent 的开发准备工作，为后续编码做好骨架和环境基础。

可以概括为：

> 为一个真正能调用 Tool 的 Agent 准备好最小开发环境。

---

## 第一步：环境准备

建议使用：

- Python 3.11
- 或 Python 3.12

项目初始化流程如下：

```bash
mkdir my_agent
cd my_agent
```

创建虚拟环境：

```bash
python -m venv .venv
```

Windows 激活方式：

```bash
.venv\Scripts\activate
```

安装依赖：

```bash
pip install openai python-dotenv
```

这里只安装两个库，是刻意保持最小依赖。

核心原因是：

> 先理解 Agent 的底层机制，再去学习更高层的框架封装。

---

## 为什么暂时不用 LangChain

很多初学者会问，既然目标是做 Agent，为什么不一开始直接使用 LangChain、AutoGen 或其他框架？

原因是，如果一开始就直接调用：

```python
agent.run(question)
```

虽然很快能跑通，但学习者往往并不知道这些关键问题：

- Tool Schema 是什么时候生成的
- Tool Call 是什么时候返回的
- Agent Loop 是怎么循环的
- Tool 为什么能“自动”调用

这会让 Agent 看起来像魔法。

但实际上：

> Agent 一点都不神奇，它只是把一套可解释的流程封装起来了。

所以本阶段故意只使用：

- `openai`
- `python-dotenv`

目的是把每一个底层环节都看清楚。

---

## 第二步：项目结构

本课沿用上一课确定的工程结构，在项目目录中创建以下文件：

```text
my_agent/
│
├── main.py
├── agent.py
├── tools.py
├── prompts.py
├── config.py
├── .env
└── requirements.txt
```

这套结构的意义在于职责分离：

- `main.py` 负责入口
- `agent.py` 负责循环与调度
- `tools.py` 负责工具实现
- `prompts.py` 负责系统提示词
- `config.py` 负责配置
- `.env` 负责环境变量
- `requirements.txt` 负责依赖声明

从这里开始，整个课程的代码都会尽量稳定在这套骨架上扩展。

---

## 第三步：API Key 与配置隔离

`.env` 示例：

```text
OPENAI_API_KEY=你的APIKey
OPENAI_BASE_URL=https://api.openai.com/v1
MODEL=gpt-5
```

这一层设计的意义非常大。

如果未来切换到其他服务商，例如：

- OpenAI
- Azure OpenAI
- OpenRouter
- DeepSeek
- 阿里百炼
- 硅基流动

通常只需要调整：

- `BASE_URL`
- `MODEL`

而主业务代码几乎不需要大改。

这就是为什么配置必须独立到 `config.py` 和 `.env`，而不能散落在各个业务文件里。

---

## 第四步：第一个 Tool 不只是函数

本课选择的第一个 Tool 是：

> Calculator

很多新人会先写出这样的函数：

```python
def calculator(a, b):
    return a + b
```

但在 Agent 世界里，这还远远不够。

原因是：

> Agent 不认识“裸 Python 函数”，它认识的是一个被描述清楚的 Tool。

所以一个完整 Tool，至少应包含两层：

```text
Python 函数
+ 
Tool 描述（Schema）
```

以后无论是 OpenAI Agent SDK、Claude、Gemini 还是 MCP，底层都遵循这个思路。

---

## Tool 真正重要的部分是什么

以 `calculator` 为例，一个 Tool 对 LLM 最重要的信息其实不是函数体，而是下面这些元信息：

### Name

```text
calculator
```

### Description

```text
执行数学计算
```

### Parameters

```text
expression
```

例如：

```text
18*29
```

### Return

```text
522
```

这说明一个关键事实：

> Python 函数本身通常很简单，真正决定 LLM 会不会正确调用它的，是 Tool 的描述质量。

---

## 为什么 Description 很重要

假设有两个 Tool：

### Tool A

```text
calculator
```

Description 很模糊。

### Tool B

```text
math_solver
```

Description 很清楚：

```text
用于加法、减法、乘法、除法、百分比、平方根等数学计算
```

通常模型更容易正确使用第二个 Tool。

因为模型在决定调用哪个 Tool 时，主要看的不是函数实现，而是：

- 名称
- 描述
- 参数定义

所以有一个非常重要的结论：

> Description 越准确，Agent 的工具选择能力通常越强。

---

## 第五步：理解 Schema

这是第四课最关键的技术概念。

很多人第一次接触 Function Calling 或 Tool Calling，会觉得 Schema 很抽象。

其实它本质上就是：

> 一份给模型看的接口文档。

例如天气 Tool：

如果只写函数：

```python
get_weather("上海")
```

模型并不知道：

- 参数名是什么
- 参数类型是什么
- 是否必填
- 这个 Tool 适用于什么场景

所以必须明确告诉模型：

```json
{
  "name": "get_weather",
  "description": "查询城市天气",
  "parameters": {
    "city": "string"
  }
}
```

这就是 Schema。

因此可以把 Tool Schema 理解为：

> API 文档 + 参数说明

未来无论在 OpenAI、Claude、Gemini 还是 MCP 中，都会看到这种思想的不同变体。

---

## Agent 开发中的三个世界

这一节是本课最重要的认知图。

```text
        用户世界
           │
           ▼
    "帮我算18×29"

────────────────────

        LLM世界
           │
           ▼
"应该调用calculator"

────────────────────

      Python世界
           │
           ▼
calculator("18*29")

────────────────────

       Tool结果
           │
           ▼
522

────────────────────

        LLM世界
           │
           ▼
生成自然语言

────────────────────

       用户世界
```

这张图强调：

- 用户世界使用自然语言表达需求
- LLM 世界负责理解意图并做出调用决策
- Python 世界负责真正执行函数
- Tool 结果再返回给 LLM，由 LLM 组织最终回答

很多初学者学不会 Agent，不是因为不会写代码，而是因为把这三个世界混在了一起。

所以以后一定要清楚区分：

- 用户世界：自然语言
- LLM 世界：决策与结构化调用意图
- Python 世界：真实执行环境

---

## 本课作业的真正意义

本课要求做的事情看起来只是环境准备：

1. 安装 Python 3.11+
2. 创建 `my_agent` 项目
3. 创建虚拟环境
4. 安装 `openai` 和 `python-dotenv`
5. 创建项目目录结构

但这些并不是机械操作，而是在建立一种正确的开发起点：

- 从一开始就做好工程结构
- 从一开始就隔离配置
- 从一开始就只保留最小依赖
- 从一开始就按照 Tool + Schema 的思路开发

---

## 本课最重要的几个结论

### 1. Agent 开发不是先学框架，而是先理解底层

框架只是封装，不是本质。

### 2. 一个 Tool 不是单纯的 Python 函数

它还必须有模型可理解的 Schema。

### 3. Schema 本质是接口文档

它负责告诉模型工具的用途、参数和调用方式。

### 4. Description 非常关键

模型主要依靠它来判断什么时候该调用某个 Tool。

### 5. 要区分三个世界

- 用户世界
- LLM 世界
- Python 世界

这是理解整个 Agent 系统的关键。

---

## 下一课预告

下一课将进入真正的编码实现，内容包括：

- 创建 `config.py`
- 编写第一个 `tools.py`
- 定义第一个 Tool Schema
- 调用 OpenAI Responses API
- 接收并解析 Tool Call
- 实现第一个可运行的 Agent Loop

到那时，系统就会从“搭环境”正式进入“能跑起来”的阶段。

