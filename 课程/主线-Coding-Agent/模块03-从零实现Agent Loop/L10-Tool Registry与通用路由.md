# L10 Tool Registry 与通用路由：让循环不认识具体工具

> 建议学习时间：60–90 分钟。本课只重构工具路由，不增加多 Tool 并发或工程化 ToolManager。

## 1. 本节要解决的真实问题

最直接的工具执行代码会不断增加 `if name == "calculator"`、`elif name == "time"`。每新增工具都修改 Agent Loop，工具异常和结果格式也散落在分支里。Loop 本应只关心“执行这次调用并得到 Observation”，不应了解每个业务函数。

Tool Registry（工具注册表）用名称到 Callable 的映射隔离路由。本课目标是让 `run_agent` 对 calculator、time 或未来 read_file 使用同一执行流程。

## 2. 前置回顾与问题链

L09 已解决“运行几轮”，但尚未解决“如何找到函数”。继续追问：名称不存在怎么办？参数不是字典怎么办？Handler 抛异常怎么办？不同工具如何返回统一结果？

```text
ToolCall(name, arguments)
        ↓ Registry lookup
Callable(**arguments)
        ↓ normalize
Tool Observation(status, output/error)
```

## 3. 类比与两个案例

Registry 像电话簿：名字用于查找，号码对应实际处理器。电话簿不会决定应该联系谁，也不会替接听者完成工作。

案例一：`calculator` 接受 expression，返回 `42`。案例二：`read_file` 接受 path，可能抛文件错误。Loop 不需要知道数学或文件系统，只消费统一 status。

## 4. 从分支路由到数据路由

```python
# before
if call.name == "calculator":
    output = calculator(**call.arguments)
elif call.name == "time":
    output = current_time(**call.arguments)
```

```python
# after
TOOLS = {
    "calculator": calculator,
    "time": current_time,
}
handler = TOOLS.get(call.name)
output = handler(**call.arguments)
```

字典消除了业务名称分支，但校验与错误转换仍必须存在。

## 5. 本课核心：`execute_tool` 边界

```python
def execute_tool(call, tools):
    if not isinstance(call.arguments, dict):
        return {"call_id": call.id, "name": call.name,
                "status": "invalid_arguments"}
    handler = tools.get(call.name)
    if handler is None:
        return {"call_id": call.id, "name": call.name,
                "status": "unknown_tool"}
    try:
        output = handler(**call.arguments)
        return {"call_id": call.id, "name": call.name,
                "status": "success", "output": str(output)}
    except Exception as error:
        return {"call_id": call.id, "name": call.name,
                "status": "error", "error": str(error)}
```

参数形状、名称查找、执行和异常标准化都集中在一个边界。正式 Runtime 会在模块 4 把它升级为 `ToolManager.execute() -> ToolResult`。

## 6. 错误直觉与纠正

### 误区一：Registry 会自动验证 JSON Schema

字典只映射名称。参数类型和业务约束仍需 Schema 或处理器校验。

### 误区二：捕获 Exception 就代表错误处理完善

教学实现将异常转成文本，生产系统还需区分拒绝、超时和执行失败，并避免泄露敏感信息。

### 误区三：把所有系统函数注册最方便

暴露能力越多，攻击面和选择歧义越大。Registry 应只包含当前 Agent 必需的最小工具集。

## 7. 完整运行轨迹

```text
ToolCall: name=calculator arguments={'expression': '6 * 7'}
Registry: calculator -> Python handler
Handler: calculator(expression='6 * 7')
Observation: status=success output=42
Next model request: function_call_output(call_id=c1, observation)
Finish: answer=42
```

名称未找到时轨迹变为 `status=unknown_tool`，Loop 仍可把它交给模型，而不是 Python `KeyError` 崩溃。

## 8. 完整递增代码

源码位于 [l10_tool_registry.py](../../../agent-from-scratch/course-checkpoints/03-agent-loop/steps/l10_tool_registry.py)。

```python
TOOLS = {
    "calculator": lambda expression:
        "42" if expression == "6 * 7" else "unsupported",
}

model = ScriptedModel([
    ModelResponse(tool_calls=[
        ToolCall("c1", "calculator", {"expression": "6 * 7"})
    ]),
    ModelResponse("42"),
])
result = run_agent("calculate", model, TOOLS)
print(result["tool_results"][0])
```

## 9. 逐段解释

Registry 作为 `run_agent` 参数传入，而不是隐藏的全局唯一状态，因此不同 Agent 可以拥有不同能力。调用使用关键字展开 `**arguments`，使参数名与 Schema 对齐。所有 output 转成字符串，保持 Function Call Output 可序列化。

教学版结果是字典，便于初学者观察；模块 4 使用不可混淆的 dataclass。现在不提前抽象，是为了先看清路由行为。

## 10. 运行与故障实验

```powershell
python agent-from-scratch/course-checkpoints/03-agent-loop/steps/l10_tool_registry.py
```

故障实验：删除 calculator 注册，确认 unknown_tool；把 arguments 改成列表，确认 invalid_arguments；让 handler 抛 `ValueError`，确认 status=error；注册一个危险删除函数，思考为什么“可注册”不代表“应暴露”。

## 11. 练习与挑战

基础练习：新增 deterministic time 工具，不改 `run_agent`。第二项练习：新增 divide 并处理除零错误。进阶挑战：为 Registry 同时保存 description 和 handler，生成可提供给模型的工具名列表。

答案见 [模块练习参考答案](模块练习参考答案.md)。

## 12. 自测、总结与下一课

1. Registry 消除了哪类耦合？
2. 未知 Tool 为什么应成为 Observation？
3. 为什么参数校验不能只靠字典查找？
4. 为何不同 Agent 可能需要不同 Registry？
5. 工具数量越多为什么不一定越好？

下一课 [L11 多 Tool 与同轮多调用](L11-多Tool与同轮多调用.md) 将处理一个 Response 同时包含多个 Tool Call 的情况。
