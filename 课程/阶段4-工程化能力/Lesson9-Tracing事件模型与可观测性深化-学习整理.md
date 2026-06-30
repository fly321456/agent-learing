# Lesson9：Tracing 事件模型与可观测性深化

## 1. 本课目标

前面在工程化阶段里，我们已经逐步补上了很多“能运行”所需的能力：

- Logging 初版
- Tracing 初版
- Retry / Timeout
- Config 管理
- Token 与上下文管理
- Memory 分层与写入注入策略

但是到这里，一个真正的工程问题会越来越明显：

> **Agent 出了问题时，你到底怎么查？**

很多 Demo 项目在“正常跑通”时都没问题。

但一旦进入真实复杂任务，很快就会出现下面这些场景：

- 为什么这轮没有调用 Tool？
- 为什么调用了错误的 Tool？
- 为什么重复执行了同一个步骤？
- 为什么 Memory 被错误写入了？
- 为什么 Agent 在第 8 轮开始跑偏？
- 为什么同一个输入，有时成功、有时失败？

如果你只能看到最后一句 `response.output_text`，那几乎无法排查这些问题。

所以这一课我们要正式升级认知：

> **Agent 的运行过程，必须被看成一条可观察的事件流。**

这就是 Tracing 真正的工程意义。

---

## 2. 为什么普通日志不足以支撑复杂 Agent 排障

很多项目的第一版日志大概是这样：

```text
start agent
call llm
call tool
done
```

这当然比没有日志好。

但在复杂 Agent 里，这种日志很快就不够用了。

因为 Agent 不是一个线性的短函数，而是一个多轮循环系统。

它内部会发生很多不同类型的事情：

- 用户输入进入
- 上下文组装
- LLM 请求发出
- LLM 响应返回
- Tool Call 解析
- Tool 执行
- Tool Result 回填
- Memory 读取
- Memory 写入
- Summary 压缩
- 错误重试

如果这些事件只是零散日志，而没有结构化关系，那么你能看到“发生过”，却很难回答：

> **它们是按什么顺序发生的？属于哪一轮？由哪个步骤触发？耗时是多少？失败点在哪里？**

所以：

> **普通日志解决“看见点”，Tracing 解决“看见流”。**

---

## 3. 这一课最重要的一句话

请记住：

> **Tracing 的本质，不是多打几行日志，而是给 Agent 运行过程建立结构化事件时间线。**

这句话很重要。

因为很多人把 tracing 理解成“更详细的 logging”。

这不准确。

更准确地说：

### Logging

更像：

> 某个时间点发生了一条记录

---

### Tracing

更像：

> 一整次任务运行过程中，发生了一串有因果关系的事件

所以 tracing 关注的不只是“内容”，而是：

- 顺序
- 层级
- 关联
- 耗时
- 状态变化

这正是 Agent 排障最需要的东西。

---

## 4. 为什么 Agent 天生适合事件流建模

你回忆一下前面我们讲过的 Agent 本质：

```text
User
  ↓
Runner
  ↓
LLM
  ↓
Tool?
  ↓
Tool Result
  ↓
LLM
  ↓
...
```

这本身就不是一个“单点行为”，而是一个持续运行的状态机。

既然它是状态机，那么最自然的观测方式就不是“打印最终结果”，而是：

> **把每次状态转移记录为事件。**

例如：

- `run_started`
- `messages_built`
- `llm_requested`
- `llm_responded`
- `tool_selected`
- `tool_started`
- `tool_finished`
- `memory_loaded`
- `memory_saved`
- `run_finished`

这就是事件模型的起点。

---

## 5. 什么叫“事件模型”

你可以把它先理解成：

> **为 Agent 运行中发生的关键动作定义统一的事件类型。**

例如，一个事件至少可以包含下面这些字段：

- `event_type`
- `timestamp`
- `run_id`
- `turn_id`
- `status`
- `payload`

这样一来，你记录的就不再是一段随意文本，而是一条有结构的运行事实。

例如：

```json
{
  "event_type": "tool_finished",
  "timestamp": "2026-06-30T20:15:10",
  "run_id": "run_001",
  "turn_id": 3,
  "status": "success",
  "payload": {
    "tool_name": "read_file",
    "duration_ms": 28
  }
}
```

这和简单写一句：

```text
tool done
```

在工程价值上完全不是一个层级。

---

## 6. 为什么 `run_id` 和 `turn_id` 很关键

这是很多初学者会忽略，但一旦系统复杂就必不可少的设计点。

### `run_id`

用于标识：

> **同一次 Agent 执行任务**

例如一次“帮我分析项目”的完整运行。

---

### `turn_id`

用于标识：

> **运行过程中的第几轮循环**

例如：

- 第 1 轮 LLM 判断
- 第 2 轮 Tool 调用后再次判断
- 第 3 轮 继续推理

如果没有这些字段，日志一多你就很难知道：

- 哪些事件属于同一次 run
- 哪些事件属于哪一轮
- 问题究竟发生在第几步

所以：

> **Tracing 一旦进入工程阶段，必须有运行级和轮次级的关联键。**

---

## 7. 第一版事件类型应该怎么设计

这一课不追求一步到位。

我们先建立一个最小有用集合。

第一版你完全可以先定义下面这些事件：

### Run 级事件

- `run_started`
- `run_finished`
- `run_failed`

---

### Turn 级事件

- `turn_started`
- `turn_finished`

---

### LLM 级事件

- `llm_request_started`
- `llm_request_finished`
- `llm_request_failed`

---

### Tool 级事件

- `tool_call_detected`
- `tool_execution_started`
- `tool_execution_finished`
- `tool_execution_failed`

---

### Memory 级事件

- `memory_loaded`
- `memory_saved`

---

### Context 级事件

- `context_truncated`
- `context_summarized`

这个粒度已经足够支撑你当前项目的可观测性升级。

---

## 8. 为什么事件命名要稳定、统一

这一点看起来小，实际上非常重要。

很多项目最开始喜欢这样写：

- `start llm`
- `llm start`
- `begin request`
- `tool ok`
- `tool fail`

短期看能用，但长期会出问题：

- 很难统一统计
- 很难筛选同类事件
- 很难做自动分析

所以事件命名最好从一开始就规范化，例如统一使用：

```text
domain_action_status
```

比如：

- `llm_request_started`
- `llm_request_finished`
- `tool_execution_failed`

这样你后面无论是写日志分析、做可视化、还是接 tracing 平台，都会轻松很多。

---

## 9. Tracing 里最重要的不只是“发生了什么”，还有“花了多久”

很多时候 Agent 的问题不是功能错误，而是性能问题。

例如：

- LLM 很慢
- 某个 Tool 特别慢
- 某一轮消息构造太重
- Memory 查询越来越慢

所以 tracing 里最好能记录 duration，例如：

- 整次 run 耗时
- 每轮 turn 耗时
- 每次 LLM 请求耗时
- 每次 Tool 执行耗时

为什么这很重要？

因为性能问题如果没有结构化耗时数据，通常只能靠猜。

而有了 tracing 以后，你可以直接回答：

> **慢，是慢在 LLM、Tool、上下文构建，还是 Memory 注入？**

这会让排障效率差一个量级。

---

## 10. Logging 和 Tracing 最好是什么关系

这也是一个很重要的工程问题。

不是说有了 tracing，logging 就没用了。

更合理的关系通常是：

### Logging

面向：

- 人类快速阅读
- 现场调试
- 简单错误信息查看

---

### Tracing

面向：

- 结构化事件记录
- 全链路分析
- 后续回放、聚合、统计

所以更好的理解不是二选一，而是：

> **Logging 是可读层，Tracing 是结构层。**

在很多成熟系统里，这两者会并存。

---

## 11. 第一版 Tracing 应该放在哪些层

这一点非常关键。

不要把 tracing 理解成“某一个文件的功能”。

它本质上是跨层能力。

### `Runner`

记录：

- run 开始 / 结束
- turn 开始 / 结束
- 是否进入下一轮

---

### `LLM`

记录：

- 请求开始
- 请求结束
- 请求失败
- 模型名
- 耗时

---

### `ToolManager` 或 Tool 执行层

记录：

- 检测到哪个 tool call
- tool 开始执行
- tool 是否成功
- tool 耗时

---

### `Session / Context`

记录：

- 是否发生裁剪
- 是否发生摘要
- 当前上下文规模

---

### `Memory`

记录：

- 加载了哪些记忆类型
- 写入了哪些稳定信息

你会发现：

> **Tracing 不是某一个类，而是整个 Agent Runtime 的横切能力。**

---

## 12. 第一版别急着接平台，先把事件结构做对

很多人一学 tracing 就急着想：

- Jaeger
- OpenTelemetry
- Langfuse
- Arize
- Phoenix

这些平台都很重要，但不是当前第一步。

当前更重要的是：

> **先把本地事件模型建立起来。**

为什么？

因为如果你本地事件结构都不清楚，接任何平台都只是“把混乱上传到云端”。

所以第一版最值得做的是：

1. 定义统一事件结构
2. 定义统一事件类型
3. 在关键路径打点
4. 能按 `run_id` 和 `turn_id` 回放

这比直接接平台更有价值。

---

## 13. 一个很实用的第一版实现思路

在你当前课程阶段，可以先设计一个最小版 `Tracer`：

```python
class Tracer:
    def emit(self, event_type, run_id, turn_id=None, status="info", payload=None):
        ...
```

然后把事件先记录到：

- 内存列表
- 本地 jsonl 文件
- 控制台调试输出

这三个里面任选一种都可以。

第一版的重点不是平台能力，而是：

> **Agent 的关键运行步骤要变成结构化事件。**

---

## 14. 为什么“可回放”是 tracing 的高级价值

当 tracing 做得足够好时，你不只是“知道出错了”，而是可以：

> **按时间顺序重新看一遍这次 Agent 是怎么跑的。**

这意味着你可以回答很多以前回答不了的问题：

- 是先读了哪个文件？
- 第几轮开始跑偏？
- 是 Memory 注入错了，还是 Tool 结果误导了模型？
- 为什么这次执行比上次慢了 4 倍？

一旦系统进入真实开发，这种能力非常值钱。

因为复杂 Agent 的 bug 往往不是单点 bug，而是：

> **一连串步骤组合起来后出现的问题。**

而 tracing 正是用来理解这条链路的。

---

## 15. 这一课背后的核心工程思想

这一课表面在讲 tracing。

但它真正训练的是一个非常成熟的工程认知：

> **复杂系统必须是可观察的，否则就不可维护。**

Agent 尤其如此。

因为 Agent 相比普通 CRUD 程序，有几个天然更难查的问题：

- 输出不稳定
- 多轮链路长
- 工具执行分支多
- 上下文和记忆都会影响结果

所以：

> **Agent 的可观测性不是锦上添花，而是系统走向可靠性的前提。**

---

## 16. 当前阶段建议怎么落地

这一课不要贪多，建议你只做下面 4 件事：

### 第一件

定义统一事件结构。

至少包含：

- `event_type`
- `timestamp`
- `run_id`
- `turn_id`
- `status`
- `payload`

---

### 第二件

定义第一版事件类型集合。

至少覆盖：

- run
- turn
- llm
- tool

---

### 第三件

在 `Runner`、`LLM`、Tool 执行层打关键事件点。

---

### 第四件

让事件支持按 `run_id` 回看。

哪怕第一版只是写到本地文件，也已经很有价值。

---

## 17. 本课小结

今天最重要的三句话：

### 第一

> **Tracing 的本质不是多打几行日志，而是给 Agent 建立结构化事件时间线。**

### 第二

> **Logging 看见点，Tracing 看见流。**

### 第三

> **复杂 Agent 如果不可观察，就几乎不可维护。**

---

## 18. 本课作业

请你完成下面 4 个任务：

### 任务 1

设计一个最小版事件结构，至少包含：

- `event_type`
- `run_id`
- `turn_id`
- `timestamp`
- `status`
- `payload`

---

### 任务 2

为 `Runner` 增加：

- `run_started`
- `turn_started`
- `turn_finished`
- `run_finished`

事件。

---

### 任务 3

为 LLM 请求和 Tool 执行分别补：

- started
- finished
- failed

事件。

---

### 任务 4

思考并回答：

> 为什么“能看到最终答案”并不等于“系统是可观测的”？

---

## 19. 下一课预告

下一课我们继续沿着这条工程主线推进，进入：

> **Lesson10：Agent 调试方法论与故障定位流程**

到那时我们会把前面的 logging、tracing、memory、tool、context 这些模块真正串起来，回答一个更接近企业现场的问题：

> **当一个 Agent 结果不对时，应该按什么顺序排查？**

这会让你从“会搭系统”再向前一步，走到“会维护系统、会定位问题”的层次。
