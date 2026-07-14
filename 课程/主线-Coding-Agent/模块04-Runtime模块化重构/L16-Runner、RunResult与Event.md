# L16 Runner、RunResult 与 Event：重新接回闭环，但不重新混成一团

> 建议学习时间：60–90 分钟。本课完成模块 4 的标准包检查点，重点是运行级协议与事件顺序。

## 1. 本节要解决的真实问题

经过 L13–L15，我们有 Agent 配置、模型边界和工具边界，但它们还没有组成完整 Agent。现在 Runner 必须协调模型调用、工具执行、Observation 回传和终止。若 Runner 最后仍返回裸字符串，CLI 无法展示过程，测试无法断言工具失败，Session 也不知道保存到哪一步。

本课解决两个问题：`Runner.run()` 如何只负责编排而不侵入供应商或 Tool 内部？`RunResult` 如何完整表达一次运行的终态，而 `Event` 如何表达运行中的有序事实？

问题链是：最终 content 为空就一定失败吗？Tool Results 应累计还是只保留最后一轮？事件序号为何不能每轮重置？`finish_reason` 与模型单轮 reason 是否相同？CLI 若要边执行边显示，Runtime 应把 print 写死在 Loop 里吗？

## 2. 前置回顾：四个组件重新组合

```text
Agent:       静态配置和能力
BaseLLM:     一次模型调用 → LLMResponse
ToolManager: 一次工具执行 → ToolResult
Runner:      多轮编排 → RunResult + Events
```

模块化不是把程序拆散后结束，而是让组件通过明确类型重新连接。Runner 是编排者，不是万能实现者：它不解析供应商 `response.output`，不直接调用任意 handler，不把结果格式化成终端颜色，也不保存全局会话。

本课检查点仍是同步离线实现。流式 Event Sink、Session、Checkpoint 和 Retry 会在后续模块加入，但 Event 数据结构现在就必须稳定地保留顺序和 run_id。

## 3. 两个案例：裸字符串丢失了什么

案例一：Agent 调 calculator 得到 42，最终模型回答“42”。返回字符串看似足够，但调用者不知道模型用了几步、是否真的调用工具、有哪些中间结果。若工具结果错误而模型仍输出文本，更无法追查。

案例二：模型持续请求 echo，两个 Tool 都 success，却达到 `max_steps`。最终 content 是空字符串，但真正信息是 `finish_reason=max_steps`，不是“模型返回了空答案”。只有 RunResult 能同时保留步骤、工具结果和终止原因。

第三个实际场景是 CLI：它既想在执行中显示 `tool_called`，又想结束后得到完整记录。把 print 写进 Runner 会锁死界面；保存 Event 并在后续引入 sink，才能让 CLI、日志和测试各自消费相同事实。

## 4. Runner 的职责边界

Runner 负责五件事：创建一次运行状态；调用 LLM；把 continuation items 送回下一轮；通过 ToolManager 执行调用；根据协议终止并汇总结果。

Runner 不负责五件事：定义 Agent 身份；解析供应商原始 SDK；实现工具业务；判断自然语言答案质量；直接渲染 UI。

```text
Task → Runner → LLMResponse
                 ├─ no calls → finish
                 └─ ToolCalls → ToolManager → ToolResults
                                      ↓
                       function_call_output → next model step
```

一个清晰的编排层通常代码不长，却掌握执行顺序。它的正确性主要靠状态机测试，而不是靠 Prompt 期待。

## 5. 本课唯一代码增量：运行级结果

```python
@dataclass
class RunResult:
    content: str
    events: list[Event]
    tool_results: list[ToolResult]
    steps: int
    finish_reason: FinishReason
    run_id: str
```

`content` 是最终文本，不包含完整轨迹；`events` 保存发生顺序；`tool_results` 便于调用者直接检查行动；`steps` 是模型调用轮数；`finish_reason` 是 Run 终态；`run_id` 将同一次运行的日志关联起来。

不要把 LLMResponse 的 finish_reason 原样当作 Run reason。模型一轮返回 tool_calls 时，Run 还没结束；模型无调用时才由 Runner进入 completed。达到上限则由 Runner 产生 max_steps，这个事实模型自己并不知道。

## 6. Event：事实记录而非控制指令

```python
@dataclass(frozen=True)
class Event:
    type: str
    sequence: int
    run_id: str
    step: int
    data: dict[str, Any] = field(default_factory=dict)
```

type 表示发生了什么；sequence 是整次 Run 的严格递增序号；run_id 用于关联；step 表示发生在哪次模型轮次；data 保存该事件特有字段。Event 是已经发生的事实，不应该被消费者修改后反向控制 Runner。

为何同时需要 sequence 和 step？一个 step 内有 llm_started、llm_completed、多个 tool_called/tool_completed；step 会重复，sequence 才能恢复全序。下一轮 step 增加，但 sequence 不重置。

## 7. 两个错误直觉与反例纠正

### 误区一：既然有 events，就不需要 tool_results

调用者当然可以遍历 Event 重建 Tool Results，但每个调用方都要重复逻辑。RunResult 同时提供原始有序事实和常用聚合结果，是有意的读取便利。关键是两者由同一执行点产生，不能相互矛盾。

### 误区二：Runner 读取 `response.raw_response` 更方便

这会推翻 L14 边界。Runner 只使用 `LLMResponse.tool_calls` 和 `continuation_items`。后者可以是供应商对象，但 Runner 只 append，不读取属性。供应商改变输出结构时，只改适配器。

另一个误区是遇到任意 Tool error 就结束 Run。错误已经作为 Observation 回传，模型可能恢复。哪些状态必须终止要有明确策略，例如模块 5 的审批拒绝，而不是把所有失败混成异常。

## 8. 完整两轮运行轨迹

```text
seq=1 run_started    step=0
seq=2 llm_started    step=1
seq=3 llm_completed  step=1 tool_call_count=1
seq=4 tool_called    step=1 call_id=c1 name=calculator
seq=5 tool_completed step=1 status=success output=42
seq=6 llm_started    step=2
seq=7 llm_completed  step=2 tool_call_count=0
seq=8 run_completed  step=2 finish_reason=completed

RunResult(content="42", steps=2, tool_results=[...], events=[1..8])
```

注意模型原始 function_call item 通过 continuation_items 进入第二轮，ToolResult 又被序列化为相同 call_id 的 `function_call_output`。少任何一项，供应商续写协议都可能不完整。

## 9. 关键 Loop 逐段解释

源码见 [runner.py](../../../agent-from-scratch/course-checkpoints/04-runtime-refactor/src/course_runtime/runner.py)。开始时创建局部状态：

```python
run_id = str(uuid4())
events = []
tool_results = []
messages = [system_item, user_item]
manager = ToolManager(agent.tools)
```

每轮先调用模型并扩展 continuation；无 Tool Call 时完成；有调用时逐项执行并回传：

```python
messages.extend(response.continuation_items)
for call in response.tool_calls:
    result = manager.execute(call)
    tool_results.append(result)
    messages.append({
        "type": "function_call_output",
        "call_id": call.id,
        "output": json.dumps(asdict(result), ensure_ascii=False),
    })
```

`ensure_ascii=False` 让中文 Observation 可读；真正边界仍是可序列化 JSON 文本。循环耗尽后必须明确返回 max_steps，不能跌出函数得到 None。

## 10. 运行命令、预期输出与故障实验

```powershell
python agent-from-scratch/course-checkpoints/04-runtime-refactor/steps/l16_runner_results.py
python agent-from-scratch/course-checkpoints/04-runtime-refactor/demo.py
cd agent-from-scratch
python -m pytest -q tests/test_course_module4.py
```

预期步骤脚本输出包含：

```text
answer='The result is 42.' steps=2 tools=1 events=8 finish_reason=completed
```

故障实验：删除 `messages.extend(response.continuation_items)`，检查第二轮请求缺少什么；把 sequence 改成 step，观察同轮事件重复；让 ScriptedLLM 永远请求工具，确认 RunResult 为 max_steps 且保留两个成功 ToolResult；让响应耗尽，观察 llm_failed 与 run_completed(error) 的顺序。

## 11. 基础练习与进阶挑战

基础练习：打印所有 Event 的 sequence、type 和 step，并手绘状态机。再运行一次相同 Agent，证明两个 RunResult 的 run_id 不同、events 不共享。

进阶挑战：为 Runner 设计 `event_sink(event)` 参数，使事件产生时立即通知 CLI，同时继续累计到 RunResult。思考 sink 自身抛异常时是否应中断核心运行；先写策略与测试，不要直接加入复杂 EventBus。

答案见 [模块练习参考答案](模块练习参考答案.md)。

## 12. 自测、总结与下一模块

1. 为什么模型单轮 finish_reason 不等于 Run finish_reason？
2. Event 的 sequence 与 step 分别解决什么问题？
3. RunResult 为什么同时保留 events 和 tool_results？
4. Runner 对 continuation_items 能做什么、不能做什么？
5. 两个 Tool 都 success 时，Run 为什么仍可能 max_steps？

模块 4 完成后，我们得到标准包边界，但工具仍能访问任意路径，也没有审批和 Timeout。下一模块从 [L17 UTF-8 文件读取与路径边界](../模块05-安全Coding Tools/L17-UTF-8文件读取与路径边界.md) 开始，把抽象 Runtime 变成真正安全的 Coding Agent。
