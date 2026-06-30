# 第三课学习整理：人生第一个 Agent（从 0 到 1）

## 本课定位

从这一课开始，重点不再只是理解概念，而是进入真正的 Agent 开发者思维。

这一课刻意不写代码，而是先做架构设计。

核心原因是：

> 先设计，再写代码，才能知道每一行代码为什么存在。

很多教程一上来就直接导入 SDK、复制示例，虽然能跑通，但学习者往往并不知道背后的结构。第三课要建立的就是这种“先搭骨架，再填实现”的工程意识。

---

## 一个 Agent 至少有哪些模块

很多人对 Agent 的理解仍停留在：

```text
用户
↓
LLM
↓
答案
```

但一个真正最小可用的 Agent，至少可以拆成下面这些模块：

```text
                User
                  │
                  ▼
          ┌─────────────┐
          │   Agent     │
          └──────┬──────┘
                 │
      ┌──────────┼──────────┐
      ▼          ▼          ▼
   Prompt     Tools      Memory
      │          │          │
      └──────────┼──────────┘
                 ▼
               LLM
                 │
                 ▼
          Tool Call ?
                 │
         Yes ────┴──── No
          │             │
          ▼             ▼
   Execute Tool     Final Answer
          │
          ▼
     Tool Result
          │
          ▼
         LLM
```

这张图的意义很大，因为它说明：

- Prompt 负责约束 Agent 的行为方式
- Tools 提供实际执行能力
- Memory 提供上下文延续能力
- LLM 负责决策
- Agent 外壳负责循环和调度

以后无论是 LangChain、OpenAI Agent SDK、AutoGen 还是 ReAct，本质上都能拆回这些模块。

---

## 第一个 Agent 的目标范围

第三课设计的第一个 Agent 故意保持极简，只包含三个 Tool：

- `Calculator`
- `Read File`
- `Current Time`

### 示例 1：时间查询

用户：

```text
现在几点？
```

Agent 决策：

```python
get_current_time()
```

返回结果后，再组织自然语言答案。

### 示例 2：数学计算

用户：

```text
18 × 29
```

Agent 决策：

```python
calculator()
```

拿到结果后再回答用户。

### 示例 3：读取文件

用户：

```text
读取 hello.txt
```

Agent 决策：

```python
read_file()
```

然后返回文件内容。

虽然功能很少，但已经具备了现代 Agent 的最小雏形。

---

## 建议的项目目录结构

从一开始就要有工程化意识，不要把所有逻辑都塞进一个 `main.py`。

建议最小结构如下：

```text
my_agent/
│
├── main.py
├── tools.py
├── prompts.py
├── agent.py
└── config.py
```

这个结构背后的思想不是“为了好看”，而是为了让不同职责自然分层。

---

## 每个文件的职责

## 1. `config.py`

这里只放配置项，例如：

```python
API_KEY
BASE_URL
MODEL
```

原则是：

> 配置文件只管配置，不写业务逻辑。

这样后续切换模型、切换服务地址或调整环境变量时，影响范围最小。

---

## 2. `tools.py`

这里集中定义所有 Tool，例如：

```python
calculator()
read_file()
write_file()
get_time()
```

它的意义是把“执行能力”从 Agent 主流程里抽离出来。

这样当 Tool 越来越多时，不会把控制流和执行逻辑搅在一起。

---

## 3. `prompts.py`

这里专门放 Prompt，例如：

```text
你是一名智能助手。
当需要计算时调用 calculator。
当需要读取文件时调用 read_file。
```

为什么要单独拆出来？

因为 Prompt 在 Agent 系统里不是零散字符串，而是核心行为配置。它往往会越来越长、越来越重要，如果直接写在 `main.py` 里，后面维护成本会非常高。

---

## 4. `agent.py`

这是整个 Agent 的核心文件。

它负责的通常是：

```text
发送请求
↓
判断有没有 Tool Call
↓
执行 Tool
↓
把结果传回 LLM
↓
继续循环
↓
直到得到最终答案
```

也就是说，这里承载的是 Agent Loop，而不是某个具体业务功能。

---

## 5. `main.py`

`main.py` 应该尽量薄。

它理想中的职责只有：

```python
agent.run(user_input)
```

也就是：

- 接收用户输入
- 调用 Agent
- 打印结果

不要把业务判断、工具实现、Prompt 拼接全部写在这里。

---

## 为什么要这样设计

因为 Agent 一旦开始扩展，Tool 数量会迅速增长，例如：

- Calculator
- Weather
- Browser
- Git
- Filesystem
- Python
- SQL
- Email
- Chrome
- Excel

如果没有模块分层，最终很容易演变成一个几千行的大文件，既难维护，也难调试，更难扩展。

所以第三课其实在培养一种非常关键的习惯：

> 从第一个 Agent 开始，就按工程方式开发。

---

## Agent 最重要的一条原则：让 LLM 决策

很多新人会本能地写出这样的程序：

```python
if 用户问天气:
    调天气

if 用户问时间:
    调时间
```

这种写法的问题在于：

> 你又把 Agent 写回 Workflow 了。

Agent 的核心思想应该是：

```text
用户输入
↓
LLM 判断
↓
Tool Call
↓
执行 Tool
```

而不是程序员手写大量规则，例如：

```python
if "天气" in question:
    ...
```

这里的根本差别是：

- Workflow 强依赖开发者预设分支
- Agent 把分支决策交给模型

---

## 为什么现代 Agent 强调“薄 Controller”

很多优秀 Agent 项目都强调一个原则：

> Controller 越薄越好。

所谓薄 Controller，意思是宿主程序只做这些事：

- 把 Tool 列表提供给 LLM
- 接收 LLM 的输出
- 如果是 Tool Call，就执行 Tool
- 如果是 Final Answer，就结束

而不是在控制器里写很多业务判断：

```python
if "天气" in question:
    ...
elif "股票" in question:
    ...
elif "新闻" in question:
    ...
```

推荐的方式是：

```text
把所有 Tool 告诉 LLM
让 LLM 自己决定调用哪个
```

这就是现代 Agent 的设计思想。

Controller 负责调度，不负责替模型做决策。

---

## 本课最终沉淀的工程结构

第三课最重要的产出不是代码，而是这个最小工程骨架：

```text
my_agent/

├── main.py
├── config.py
├── prompts.py
├── tools.py
└── agent.py
```

未来的所有扩展，几乎都会建立在这个结构上。

---

## 本课真正想训练的思维

第三课留给开发者的核心思考题是：

> 为什么我们一直强调“让 LLM 决策”，而不是在 Python 里写一堆 `if...else`？

这个问题之所以重要，是因为它区分了两种完全不同的开发范式：

### 传统程序思维

开发者预先把路径写死：

```text
输入 A -> 分支 1
输入 B -> 分支 2
输入 C -> 分支 3
```

### Agent 思维

开发者只提供：

- 目标
- 可用工具
- 行为约束

然后把“下一步该怎么走”交给模型动态决定。

也就是说：

> Agent 开发者不是在写死流程，而是在设计一个可决策系统。

---

## 下一课预告

第四课将正式进入代码实现，包含：

1. 创建 Python 项目
2. 配置 OpenAI SDK
3. 编写第一个 Tool
4. 定义 Tool Schema
5. 调用 LLM 接口
6. 解析 Tool Call
7. 实现第一个 Agent Loop

到第四课结束时，就会拥有一个真正可运行的最小 Agent。

