# L13 Agent 配置边界：先拆“它是谁”，再拆“它怎样运行”

> 建议学习时间：60–90 分钟。模块 4 从本课开始由单文件教学实现走向可维护 Runtime，但不会一次展示最终架构。

## 1. 本节要解决的真实问题

模块 3 的 `run_agent()` 很适合学习闭环：一眼能看到模型、工具和循环。然而加入第二个 Agent 后，问题马上出现。代码应在哪里保存名称和 Instructions？每次运行的 Task、Observation 和 Event 是否也塞进 Agent？重试策略属于 Agent 身份还是执行器？如果 `Agent.run()` 一边保存配置、一边管理循环、一边执行工具，这个类会很快变成无法单独测试的“大管家”。

本课只解决一个问题：**Agent 配置（Agent Configuration）描述“这个 Agent 是谁、拥有什么能力”，Runner 描述“这一次怎样执行”**。我们暂不实现工具审批或 Session，先建立不会随着功能增长而倒塌的第一条边界。

问题链如下：同一个代码助手能否连续处理两个 Task？两次运行是否应共享 `events`？同一个 LLM 能否被两个不同 Instructions 的 Agent 使用？`max_steps` 是静态安全上限还是某一步的当前计数？回答这些问题，才能决定数据放在哪里。

## 2. 前置回顾与从单文件发现变化轴

模块 3 的函数签名大致是：

```python
run_agent(task, model, tools, max_steps=5)
```

它把四种变化放在同一层：`task` 每次调用都变；`model` 和 `tools` 通常随 Agent 配置变化；`max_steps` 是安全策略；`trace`、`tool_results` 和当前 step 是运行中产生的状态。单文件阶段这样写最直观，模块化阶段则要按生命周期拆分。

```text
较稳定：name / instructions / llm / tools / max_steps
每次变化：user_input / run_id / current_step / events / tool_results
```

“先找变化轴，再定义类”比“看到很多函数就创建类”更可靠。类不是文件整理工具，而是责任和生命周期的边界。

## 3. 生活类比与两个 Coding Agent 案例

把 Agent 想成一位值班开发者的岗位说明：姓名、工作原则、可使用的工具和单次任务上限写在岗位卡上；今天收到的故障单、执行过的命令和处理记录写在工单里。岗位卡不会因为处理第二张工单而混入第一张工单的日志。

案例一：`reviewer` 的 Instructions 是“只审查，不修改”，Tools 只有读取和搜索。案例二：`fixer` 的 Instructions 是“先定位、再补丁、最后测试”，Tools 还包括写入和命令。两者可以使用同一个 LLM 实现，却不能共享同一份工具集合和指令。

另一个案例是连续运行：同一个 `reviewer` 先检查仓库 A，再检查仓库 B。Agent 配置可以复用，但 `run_id`、事件列表和结果必须重新创建，否则第二次报告会夹带第一次的轨迹。

## 4. 概念推导：配置、依赖与运行状态

我们把数据分成三组：

| 分组 | 例子 | 生命周期 |
| --- | --- | --- |
| Agent 配置 | name、instructions、llm、tools、max_steps | 多次运行可复用 |
| Runner 依赖 | 事件接收器、重试策略、检查点存储 | 由执行环境提供 |
| Run 状态 | task、run_id、step、events、tool_results | 一次运行创建并结束 |

本课的教学 `Agent` 只包含第一行。第二行会在后续模块逐渐进入 Runner，第三行必须在 `Runner.run()` 内创建。这样做不是为了追求“纯架构”，而是为了获得三个可验证结果：Agent 可以独立校验；Runner 可以用同一个 Agent 重复运行；Run 状态不会串线。

```python
@dataclass(frozen=True)
class Agent:
    name: str
    instructions: str
    llm: BaseLLM
    tools: list[ToolSpec] = field(default_factory=list)
    max_steps: int = 5
```

`frozen=True` 表达配置创建后不应在运行中偷偷变化。它不是绝对安全机制，但会阻止常见的误赋值。

## 5. 本课唯一代码增量

L13 只把稳定配置收进 `Agent`，不搬运完整 Loop。最小步骤脚本先使用一个简化 `AgentConfig`：

```python
@dataclass(frozen=True)
class AgentConfig:
    name: str
    instructions: str
    max_steps: int = 5

config = AgentConfig("repo-helper", "Inspect before editing.", 4)
```

随后检查 `hasattr(config, "run")` 为 False。这不是缺功能，而是刻意证明配置对象没有执行职责。模块最终代码再把 `llm` 与 `tools` 作为能力依赖加入，源码见 [agent.py](../../../agent-from-scratch/course-checkpoints/04-runtime-refactor/src/course_runtime/agent.py)。

## 6. 两个错误直觉与反例纠正

### 误区一：面向对象就是把 `run_agent` 改成 `Agent.run`

方法位置改变了，责任并没有改变。若 `Agent.run()` 同时生成 run_id、累计事件、重试 LLM、执行命令和写检查点，测试一个配置校验也要构造整个世界。真正的模块化是分离变化原因，不是把函数缩进到类里。

### 误区二：所有参数都做成全局环境变量最省事

全局配置让测试互相污染，也无法在同一进程创建 reviewer 与 fixer。环境变量适合应用启动时读取，读取后应转换为显式对象。Agent 核心对象不应在运行中四处调用 `os.getenv()`。

还有一个常见误区：把对话历史放进 Agent 字段。这样同一 Agent 无法安全服务两个 Session，并发运行更会相互覆盖。历史属于 Session 或一次 Run 的输入，不属于身份配置。

## 7. 手工运行轨迹：同一配置，两次独立运行

```text
AgentConfig(repo-helper, max_steps=4)
Run A: task="inspect repository A" → run_id=A → events=[A1, A2, ...]
Run B: task="inspect repository B" → run_id=B → events=[B1, B2, ...]
Invariant: AgentConfig 未改变，A.events 不出现在 B
```

如果把 `events=[]` 写成 Agent 的可变字段，两次运行就会共享它；如果把 current_step 写进 Agent，异常退出后下一次运行可能从错误 step 开始。边界设计的价值正体现在这些并不华丽、却很难排查的状态错误上。

## 8. 修改前后代码差异

模块 3 的调用者把全部零件逐项传给函数：

```python
result = run_agent(task, model, tools, max_steps=5)
```

模块 4 的目标形态分两步：

```python
agent = Agent("repo-helper", "Inspect before editing.", llm, tools, max_steps=5)
result = Runner().run(agent, task)
```

前者不是错误，后者也不是天然高级。只有当项目需要多个 Agent 配置、多个运行和独立测试时，这次拆分才开始回本。课程选择此时重构，是因为模块 3 已经用测试固定了 Loop 行为，重构有可比较基线。

## 9. 关键代码逐段解释

`name` 用于事件和展示，不承担模型行为；真正影响模型的是 `instructions`。`llm` 是符合接口的对象，不限定供应商。`tools` 是声明列表，执行路由由下一课之后的组件处理。`max_steps` 是每次运行采用的上限，当前计数绝不能写回该字段。

```python
def __post_init__(self) -> None:
    if not self.name.strip():
        raise ValueError("Agent name cannot be empty")
    if self.max_steps < 1:
        raise ValueError("max_steps must be at least 1")
```

配置错误应在创建时尽早失败，而不是 Loop 跑到一半才发现。这里不验证 Instructions “写得好不好”，因为那是评测问题，不是结构校验能可靠判断的事实。

## 10. 运行命令、预期输出与故障实验

```powershell
python agent-from-scratch/course-checkpoints/04-runtime-refactor/steps/l13_agent_configuration.py
```

预期输出：

```text
agent=repo-helper max_steps=4 has_run=False
```

故障实验一：把 `max_steps` 改成 0，并在模块最终 `Agent` 中创建对象，观察它立即抛出 `ValueError`。故障实验二：尝试执行 `agent.max_steps = 99`，理解 frozen dataclass 防止的是什么。故障实验三：自行把 `events` 加为字段并连续 append 两次，观察为什么这会污染下一次运行。

## 11. 基础练习与进阶挑战

基础练习：创建 `reviewer` 与 `fixer` 两个配置，列出它们不同的 Instructions 与 Tool 权限。再写一个纯函数 `describe_agent(agent)`，只读取配置，不触发模型调用。

进阶挑战：判断以下字段应归 Agent、Runner 依赖还是 Run 状态：temperature、workspace、retry_attempts、session_id、current_step、approval_callback。不要急着编码，先写理由；同一个字段在不同产品中可能有不同归属，关键是说明生命周期和变化原因。

答案见 [模块练习参考答案](模块练习参考答案.md)。

## 12. 自测、总结与下一课

1. 为什么 `Agent.run()` 不一定是好的面向对象设计？
2. Agent 配置与 Run 状态最关键的生命周期差异是什么？
3. 为什么 `current_step` 不应放进可复用 Agent？
4. 同一个 LLM 对象能否服务两个 Agent 配置，取决于什么？
5. 配置校验与答案质量评测为什么不能混为一谈？

本课没有增加 Agent 能力，只减少了未来状态混乱的可能。下一课进入 [L14 LLM 接口与 LLMResponse](L14-LLM接口与LLMResponse.md)，解决供应商响应如何被 Runtime 消费而不泄漏到每一层。
