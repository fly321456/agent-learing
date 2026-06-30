# 第十课学习整理：进入真正的 Agent 工程开发

## 本课定位

从这一课开始，课程正式进入：

> 真正的 Agent 工程开发阶段

这一课最重要的变化，不是新增了某个 API，而是学习方式和工程目标发生了升级。

课程明确指出了前面阶段的一个问题：

> 理论虽然正确，但比例过高

如果继续这样，最终很容易变成：

> 会讲 Agent，但不会开发 Agent

因此从第十课开始，课程全面切换到：

```text
10% 理论
90% 编码
```

也就是典型的 `Project Driven Learning`。

---

## 课程目标再次升级

课程后半段不再以“理解概念”为主要目标，而是围绕一个真实项目持续构建：

> 做一个类似 Claude Code 的 Coding Agent

目标交互形态大致如下：

```text
你：
帮我分析 SpringBoot 项目

Agent：
思考
↓
ls
↓
find pom.xml
↓
read pom.xml
↓
grep Controller
↓
分析代码
↓
输出报告
```

这里最重要的不是“像不像 Claude Code”，而是：

> 我们开始以真实 Coding Agent 的工程方式来组织系统

---

## 项目结构开始成形

从这一课开始，后续课程将围绕下面这个项目结构逐步实现：

```text
coding_agent/

├── app.py
├── agent.py
├── runner.py
├── llm.py
├── tool_manager.py
├── tools/
├── prompts/
└── config.py
```

这个结构并不是随意设计的，而是刻意贴近现代 Agent Framework 的职责拆分方式。

它与 OpenAI Agents SDK 的设计思想已经非常接近。

这里有几个关键模块：

- `agent.py`：描述 Agent 本体
- `runner.py`：负责运行时循环
- `llm.py`：负责统一模型接口
- `tool_manager.py`：负责工具注册与执行
- `tools/`：存放具体 Tool
- `prompts/`：存放 Prompt 模板
- `config.py`：存放配置

这说明课程已经正式从“单个脚本”转向“可演进工程”。

---

## 第一步：为什么要封装 LLM

这一课提出了一个非常典型、也非常工程化的问题：

很多新人会把这种调用写得到处都是：

```python
response = client.responses.create(...)
```

在 Demo 阶段这没有问题，但一旦模型提供方发生变化，问题就会暴露出来。

例如：

- 今天用 `GPT-5`
- 明天换 `Claude`
- 后天换 `Qwen`

如果业务代码里到处直接写 OpenAI 的调用方式，那么替换模型时就需要全局修改，成本非常高。

所以要引入：

```text
llm.py
```

把所有模型调用统一封装到一个抽象层中。

目标是让业务代码以后都只面对：

```python
llm.generate(...)
```

这样如果未来替换模型，只需要改一处实现，而不是改整个项目。

这就是非常典型的：

> 抽象（Abstraction）

---

## 第二步：设计 LLM 类

课程建议不要让业务层直接依赖 OpenAI SDK，而是先定义一个更稳定的接口：

```python
class LLM:

    def generate(self, messages, tools):
        ...
```

这一层设计非常关键。

因为从业务角度看，无论底层是：

- OpenAI
- Claude
- Gemini
- Qwen

业务真正需要的都只是同一件事：

> 给模型上下文和工具，拿回响应

也就是说，对上层系统而言，“生成一次响应”才是稳定能力，而不是某家 SDK 的具体调用细节。

所以 `generate()` 的意义在于：

- 对外暴露统一接口
- 对内隐藏不同模型厂商差异

这就是：

> 统一接口（Interface）

---

## 第三个真正重要的架构认知

这一课特别强调了一个很容易被忽略的点：

很多人脑子里的结构仍然是：

```text
Agent
↓
OpenAI
```

但更合理的架构应该是：

```text
Agent
↓
LLM Interface
↓
OpenAI
```

这意味着：

- Agent 不依赖某家具体厂商
- Agent 只依赖统一接口
- 具体模型实现放到接口下层

这正是经典的软件设计原则：

> 依赖倒置原则（Dependency Inversion Principle）

也就是高层模块不应直接依赖低层细节，而应依赖抽象。

在这里：

- 高层模块是 `Agent`、`Runner`
- 低层细节是 `OpenAI SDK`、`Claude SDK`、`Qwen SDK`
- 抽象层就是 `LLM Interface`

---

## 为什么优秀框架不会把 OpenAI 写死

这一课借这个话题，开始引导理解官方或成熟框架为什么常常显得“多包了一层”。

原因其实很简单：

> 好框架要抵抗变化

Agent 自身不应该知道自己底层到底是不是 GPT。

它只应该知道：

```python
generate()
```

就够了。

未来如果新增：

- `ClaudeLLM`
- `QwenLLM`
- `DeepSeekLLM`
- `GeminiLLM`

那么只需要这些类去实现统一接口，上层 Agent 代码无需修改。

这个能力非常重要，因为真实生产系统里，模型切换、灰度测试、多模型路由都是常见需求。

---

## 架构图：Agent 到 LLM 抽象层

课程将这种分层明确抽象为：

```text
            Agent

              │

              ▼

         LLM Interface

      ┌──────┼──────┐

      ▼      ▼      ▼

 OpenAI  Claude  Qwen
```

这个结构的价值非常高，因为它说明：

- 上层只看能力，不看厂商
- 下层可以自由扩展不同模型实现
- 替换和新增模型不影响 Agent 核心逻辑

这也是为什么成熟工程里，优秀工程师通常会先设计接口，再接具体实现。

---

## 为什么优秀工程师先设计接口

初学者常见写法是：

```python
client.responses.create(...)
```

在很多地方重复出现。

这种写法的问题不是“不能跑”，而是：

> 把业务层和具体供应商 SDK 绑死了

优秀工程师更倾向先设计：

```text
generate()
```

然后要求所有模型实现都遵守这一个统一协议。

这样做的收益包括：

- 更容易替换底层模型
- 更容易测试和 Mock
- 更容易做多模型扩展
- 更容易维持上层架构稳定

这就是典型的：

> 面向接口开发

---

## 这节课真正学的不是 OpenAI，而是软件架构

这一课虽然表面上在讨论模型调用，但真正学到的并不是某个 SDK 的用法，而是：

> 如何给 Agent 系统设计一层稳定的 LLM 抽象

因此以后看任何 Agent Framework，第一件事都可以先找：

```text
LLM 抽象层
```

如果一个框架完全没有这层抽象，通常意味着：

- 对供应商耦合较重
- 可扩展性较弱
- 架构成熟度可能不高

---

## 后续路线正式升级

这一课也把后续课程路线升级为更系统的工程成长路径：

| 阶段 | 内容 | 最终成果 |
| ---- | ---- | -------- |
| 第一阶段 | 自己实现 Agent | 一个可运行的 Agent |
| 第二阶段 | 阅读 OpenAI Agents SDK 源码 | 看懂官方实现 |
| 第三阶段 | 自己实现 MCP Client | Agent 能调用 MCP Server |
| 第四阶段 | 自己实现 RAG | Agent 能读知识库 |
| 第五阶段 | 多 Agent 协作 | Planner + Executor + Reviewer |
| 第六阶段 | Claude Code 架构分析 | 理解为什么它这么强 |
| 第七阶段 | 部署到生产 | FastAPI + Docker + 日志 + Tracing |

这条路线说明目标已经不再是“写几个 Demo”，而是：

> 建立完整的 Agent 工程能力

---

## 推荐的学习与交付方式

课程最后进一步建议采用真实项目 + Git 提交的方式推进：

例如：

```text
lesson-01-init-project
lesson-02-llm-wrapper
lesson-03-tool-manager
lesson-04-agent-loop
lesson-05-memory
lesson-06-rag
lesson-07-mcp
...
```

这种方式的价值很高：

- 每一课有真实产出
- 学习轨迹可追溯
- 可以沉淀成 GitHub 作品集
- 更接近企业内培养工程师的方式

---

## 本课核心结论

### 1. 课程从这一课开始正式进入项目驱动

重点从理论理解转向工程实现。

### 2. LLM 调用应该被抽象到统一接口后面

业务层不应直接到处依赖某家模型 SDK。

### 3. `Agent -> LLM Interface -> Provider` 是成熟架构

它能有效降低耦合，提升可扩展性。

### 4. 这一课真正学到的是依赖倒置和面向接口开发

而不只是模型调用方式。

### 5. 后续课程将围绕真实项目与 Git 提交推进

从“学知识点”转为“做系统”。

---

## 下一步

从下一课开始，课程将正式进入实战模式：

- 直接创建项目
- 完成第一版可运行代码
- 每一课对应一个 Git Commit
- 采用“代码 + Code Review + 架构分析”的学习方式

这一步意味着课程正式进入更接近企业和开源项目的训练模式。

