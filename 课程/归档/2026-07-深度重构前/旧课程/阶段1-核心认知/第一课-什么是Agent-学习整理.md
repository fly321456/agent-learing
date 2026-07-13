# 第一课批改整理：什么是 Agent

## 课程核心结论

Agent 不是“更聪明的大模型”，而是：

```text
Agent = LLM（思考） + Tools（执行） + Loop（持续决策）
```

其中最关键的不是“会不会调用工具”，而是：

> Agent 在每次工具调用后，都会基于新观察结果重新思考下一步。

---

## Agent 和普通 ChatGPT 的区别

普通 LLM 更像一次性推理：

```text
Input
↓
Inference
↓
Output
```

或者：

```text
LLM
↓
产生 Token
↓
结束
```

这属于 `Single-shot`。

而 Agent 属于闭环决策：

```text
LLM
↓
Tool
↓
LLM
↓
Tool
↓
LLM
↓
Finish
```

这属于 `Closed-loop`。

所以，ChatGPT 本身通常不能算一个完整 Agent，因为它默认是“输入一次、回答一次、流程结束”，没有持续观察环境并动态决策的闭环过程。

---

## Agent 和 Workflow 的区别

一句话概括：

> Workflow 是 Human Designed（人设计流程）
>
> Agent 是 Model Designed（模型决定流程）

Workflow 的特点是固定流程：

```text
Step1
↓
Step2
↓
Step3
↓
结束
```

Agent 的特点是动态规划。不同任务、不同上下文、不同观察结果，都会导致它选择不同路径。

例如分析代码仓库时，Agent 可能会这样决策：

```text
README 有没有？
↓
没有
↓
看看 package.json
↓
哦，是 Java
↓
去找 pom.xml
↓
看看 Dockerfile
↓
看看 CI
```

重点在于：

> 每一次流程都可能不一样。

---

## Tool 为什么决定 Agent 的能力边界

最关键的一句话：

> LLM 负责“决定做什么”，Tool 负责“真正去做”。

LLM 可以决定：

- 应该读取文件
- 应该联网搜索
- 应该执行代码
- 应该结束任务

但 LLM 自己通常不能直接：

- 打开你的电脑文件
- 访问网络
- 操作浏览器
- 执行 Shell
- 运行 Python

这些能力都必须由 Tool 提供。

一个很好理解的比喻：

> LLM 是 CEO，Tool 是员工。

CEO 负责决策，员工负责执行。没有员工，CEO 决策再正确也落不了地。

---

## GitHub 项目分析 Agent 至少需要哪些能力

如果要设计一个“自动分析 GitHub 项目”的 Agent，至少应具备以下 Tool 能力：

- `Git Clone`
- `Read File`
- `Search File`
- `Edit File`
- `Execute Python`
- `Execute Shell`
- `Browser Search`
- `Markdown Parser`
- `PDF Reader`
- `Terminal`
- `Git Commit`
- `Memory`

一个典型流程可能是：

```text
clone()
↓
find("pom.xml")
↓
read("pom.xml")
↓
grep("Redis")
↓
read("application.yml")
↓
总结项目结构与技术栈
```

---

## 本课最容易忽视的核心：Observe

很多初学者会把 Agent 理解成：

```text
Think
↓
Act
↓
Done
```

但更准确的 Agent 运行模式是：

```text
Think
↓
Act
↓
Observe
↓
Think
↓
Act
↓
Observe
↓
Think
↓
Finish
```

其中 `Observe` 很关键，因为工具执行后的结果会改变后续决策。

例如：

第一次思考：

```text
应该先下载项目。
```

调用：

```python
git_clone()
```

观察结果：

```text
有 300 个文件。
```

重新思考：

```text
文件太多，先读 README。
```

所以 Agent 的本质不是“一次想完”，而是：

> 一边观察，一边决定下一步。

---

## 第二课预告

下一课将进入 Tool Calling 与实际开发，重点回答：

> LLM 是怎么知道要调用哪个 Tool 的？

将学习的内容包括：

- 为什么大模型会“自己”调用 Tool
- 什么是 Function Calling
- 什么是 Tool Calling
- 为什么 OpenAI、Claude、Gemini 的 Tool Calling 本质相近
- 一个 Tool 的基本组成：名称、描述、参数、返回值
- 手写一个约 100 行 Python 的简易 Agent

