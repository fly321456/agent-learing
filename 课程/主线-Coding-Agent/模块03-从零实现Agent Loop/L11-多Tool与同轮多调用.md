# L11 多 Tool 与同轮多调用：一个响应不等于一个动作

> 建议学习时间：60–90 分钟。本课处理一个模型响应包含多个 Function Call 的情况。

## 1. 本节要解决的真实问题

用户要求“计算 6×7，并告诉我当前时间”。模型可能在同一个 Response 中返回 calculator 和 time 两个 Tool Call。如果代码只取 `tool_calls[0]`，第二个事实会丢失；如果每执行一个就立即请求模型，会产生额外轮次，并可能破坏同轮调用的关联。

本课核心规则：**先遍历并处理本轮所有 Tool Call，逐个追加对应 Observation，再进入下一次模型调用。**

## 2. 前置知识与问题链

L10 已能通过 Registry 执行任意一个调用。继续追问：两个调用是否共享 call ID？第一个失败是否必须阻止第二个？结果顺序如何保存？同轮是否等于并发？

```text
Response step 1
  ├─ ToolCall c1 calculator
  └─ ToolCall c2 time
       ↓ execute each
  ├─ Output c1 = 42
  └─ Output c2 = 12:00
       ↓ one next model request
Response step 2: final answer
```

## 3. 类比与两个案例

同轮多调用像开发者列出一组当前就能完成的检查项：读取配置和查看测试目录。每项都有自己的工单号，完成后一起汇报。

案例一的两个工具互不依赖，可以同轮执行。案例二是“先列文件，再根据列表选择读取哪个文件”，第二步依赖第一步 Observation，不能被错误地塞进同一轮。模型协议能提出多个调用，但应用仍要理解依赖与安全。

## 4. 数据结构与顺序

```python
calls = [
    ToolCall("c1", "calculator", {"expression": "6 * 7"}),
    ToolCall("c2", "time", {}),
]
```

每个调用的 `id` 独立。`tool_results` 按响应顺序追加，便于测试和追踪。正式系统不能用工具名称关联结果，因为同一轮可能两次调用相同工具。

## 5. 本课唯一代码增量

```python
for call in response.tool_calls:
    result = execute_tool(call, tools)
    results.append(result)
    items.append({"type": "function_call", "call_id": call.id,
                  "name": call.name, "arguments": call.arguments})
    items.append({"type": "function_call_output",
                  "call_id": call.id, "output": result})
```

外层 Loop 管模型轮次，内层 Loop 管本轮调用。混淆两层会造成多余模型请求或丢失调用。

## 6. 错误直觉与纠正

### 误区一：同轮多调用就是并发执行

本课按顺序执行，确定、易调试。并发需要额外处理资源冲突、顺序和取消，不因列表里有两个元素自动成立。

### 误区二：一个 Tool 失败就应抛弃整轮

对于独立只读工具，可以记录失败并继续其他调用，让模型看到完整结果。危险写操作则可能采用更严格策略，后续模块再设计。

### 误区三：结果用 name 做键最方便

同一工具可以不同参数调用两次，名称会冲突。稳定关联必须使用 call ID。

## 7. 完整运行轨迹

```text
Step 1: model returns 2 calls
Call c1 calculator({'expression': '6 * 7'})
Result c1 success output=42
Call c2 time({})
Result c2 success output=12:00
Step 2: model receives both outputs
Finish: The answer is 42 at 12:00.
steps=2 tool_results=2
```

## 8. 完整代码

源码位于 [l11_multiple_tools.py](../../../agent-from-scratch/course-checkpoints/03-agent-loop/steps/l11_multiple_tools.py)。

```python
calls = [
    ToolCall("c1", "calculator", {"expression": "6 * 7"}),
    ToolCall("c2", "time", {}),
]
model = ScriptedModel([
    ModelResponse(tool_calls=calls),
    ModelResponse("42 at 12:00"),
])
result = run_agent(
    "two facts",
    model,
    {"calculator": lambda expression: "42", "time": lambda: "12:00"},
)
print(f"same_round_tools={len(result['tool_results'])}")
```

## 9. 逐段解释

两个 Tool Call 在同一个 `ModelResponse` 中，因此 `steps` 最终是 2 而不是 3。每个 Result 保留 call_id、name、status 和 output。第二轮请求可以看到两个调用和两个结果，模型据此综合答案。

当前实现按列表顺序执行并继续独立失败，是教学策略。正式 ToolManager 会加入审批、超时与风险状态，但同轮关联原则不变。

顺序执行还有一个教学优势：Trace 与工具列表顺序完全一致，失败可以稳定复现。若未来并发执行，完成顺序可能不同，Runtime 就必须同时保存“模型请求顺序”和“实际完成顺序”，并处理一个任务取消后其他任务是否继续。没有性能数据前，不要为了看起来高级而提前引入并发。

同轮调用还隐含“彼此不依赖”的假设。如果第二个工具的参数必须来自第一个结果，模型在得到 Observation 前不可能可靠构造参数。正确做法是先完成第一轮，再让模型基于结果提出第二轮调用，而不是让 Runtime 猜测依赖或修改模型参数。

这也是为什么本课只建立顺序执行语义：先把调用关联、观察回传和失败边界讲清楚，再讨论并发优化。

## 10. 运行与故障实验

```powershell
python agent-from-scratch/course-checkpoints/03-agent-loop/steps/l11_multiple_tools.py
```

故障实验：删除内层 `for` 只执行首项，观察结果数变 1；让 calculator 失败，确认 time 仍执行；给两个调用相同 name 不同 id，确认结果没有覆盖；交换顺序，检查 Trace 顺序同步变化。

## 11. 练习与挑战

基础练习：同轮调用 calculator 两次，参数分别为 `2+3` 和 `6*7`。第二项练习：加入一个未知 Tool，确认三个结果都保留。进阶挑战：设计“可安全并发”的判定条件，但暂不实现线程。

答案见 [模块练习参考答案](模块练习参考答案.md)。

## 12. 自测与下一课

1. 为什么不能只读取首个 Tool Call？
2. 外层 Loop 与内层 Loop 分别遍历什么？
3. 同轮多调用为什么不自动等于并发？
4. 为什么结果必须用 call ID 关联？
5. 一项失败后是否继续，取决于哪些风险因素？

下一课 [L12 终止条件与错误](L12-终止条件与错误.md) 将完成单文件 Agent 的所有停止与失败路径。
