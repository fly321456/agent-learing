# L07 Tool Schema 与 function_call：模型提出行动，程序决定是否执行

> 建议学习时间：60–90 分钟。本课只学习“描述工具并读取调用请求”，暂不执行工具。

## 1. 本节要解决的真实问题

用户问“现在几点？”模型不能可靠知道运行机器的当前时间。我们希望它选择 `get_current_time`，但模型输出“请调用时间工具”仍只是文字。应用需要机器可读的名称、参数和调用标识。

Tool Schema 描述可用能力，`function_call` 是模型返回的结构化请求。最重要的边界是：模型没有执行 Python 函数；它只提出了行动。Runtime 仍要验证名称、解析参数、检查权限并调用处理器。

## 2. 问题链与前置回顾

```text
User asks for current fact
  → Model lacks the fact
  → Application advertises a function schema
  → Model returns function_call
  → Application inspects name/arguments/call_id
  → No tool has run yet
```

如果工具没有描述，模型如何知道参数？如果参数是自然语言，程序如何稳定解析？如果同一响应有两个调用，结果如何对应？这些问题分别由 Schema、JSON arguments 和 `call_id` 解决。

## 3. Schema 的组成与边界

```python
{
    "type": "function",
    "name": "get_current_time",
    "description": "Return a deterministic local time for the teaching example.",
    "parameters": {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False,
    },
    "strict": True,
}
```

`name` 是协议标识，不是展示标题；`description` 帮助模型判断何时使用；`parameters` 是 JSON Schema；`additionalProperties: false` 拒绝未声明字段；`strict` 请求模型严格遵守定义。Schema 描述输入，不执行函数，也不保证业务权限。

## 4. 案例一：无参数时间工具

模型看到用户问题和 Schema 后，离线响应返回：

```text
type=function_call
name=get_current_time
arguments={}
call_id=call-07
```

无参数不等于没有 Schema。空对象仍表达“这个工具不接受额外输入”，比任意字典更清楚。

## 5. 案例二：文件读取工具

若工具是 `read_file(path, start_line)`，Schema 应声明字符串路径、最小行号和必填字段。模型给出 `{"path":"README.md"}` 只是候选参数；Runtime 仍需阻止 `../secret.txt`。JSON Schema 处理形状，工作区检查处理业务安全，两层不能互相替代。

## 6. 错误直觉与反例

### 误区一：Function Calling 会自动执行函数

API 返回的是 output item。Python 处理器只有在应用显式路由后才运行。本课输出 `tool_executed: false` 就是证据。

### 误区二：Schema 越宽松越智能

允许任意属性会增加歧义和攻击面。工具应小而明确，让错误尽早暴露。

### 误区三：`id` 和 `call_id` 可以随便选一个

回传 Function 结果使用的是 `call_id`。应用自己的 Trace 可以另有事件 ID，但不能混用。

## 7. 完整运行轨迹

```text
Request.tools[0].name: get_current_time
Request.tools[0].strict: true
Response.output[0].type: function_call
Response.output[0].name: get_current_time
Response.output[0].arguments: {}
Response.output[0].call_id: call-07
tool_executed: false
```

## 8. 完整代码

源码位于 [l07_tool_schema_and_function_call.py](../../../agent-from-scratch/course-checkpoints/02-tool-calling/steps/l07_tool_schema_and_function_call.py)。

```python
client = ScriptedResponsesClient([
    ScriptedResponse(output=[
        ResponseItem(
            type="function_call",
            call_id="call-07",
            name="get_current_time",
            arguments="{}",
        )
    ])
])
response = client.create(
    model="course-model",
    input="What time is it?",
    tools=[time_tool_schema()],
)
for item in response.output:
    print(item.type, item.name, item.call_id, item.arguments)
```

## 9. 逐段解释

Scripted Response 用对象模拟 SDK output item，使代码必须遍历 `response.output`，而不是假设响应只有文本。`arguments` 保持 JSON 字符串，因为解析发生在 Runtime。看到 `function_call` 后，本课只记录，不提前路由。

工具 Schema 与 Python 函数应保持一致。若 Schema 声称需要 `timezone`，处理器却不接收，模型即使完美遵守协议也会执行失败。模块 3 会由 Tool Registry 统一名称与处理器。

## 10. 运行与故障实验

```powershell
python agent-from-scratch/course-checkpoints/02-tool-calling/steps/l07_tool_schema_and_function_call.py
```

删除 `additionalProperties: false`，比较约束；把 `arguments` 改成非法 `{`，确认仅查看时不会报错，但下一课解析必须处理；把工具名改成未注册名称，预测 Runtime 应返回何种 Observation。

## 11. 练习与进阶挑战

基础练习：设计 `read_file` 的严格 Schema。第二项练习：为 calculator 声明必填 expression。进阶挑战：构造同一响应中两个 `function_call`，证明每个都有独立 `call_id`。

答案见 [模块练习参考答案](模块练习参考答案.md)。

## 12. 自测与下一课

1. Tool Schema 解决什么问题，不能解决什么？
2. `function_call` 为什么不等于工具执行？
3. `arguments` 为什么需要 JSON 解析？
4. `call_id` 在下一轮承担什么职责？
5. 严格 Schema 为什么有助于安全和测试？

下一课 [L08 执行 Tool 并回传结果](L08-执行Tool并回传结果.md) 将完成固定的两次模型调用。

## 官方核验

- 最后核验日期：2026-07-17
- [OpenAI Function calling：Strict mode](https://developers.openai.com/api/docs/guides/function-calling#strict-mode)

最终 Runtime 使用 `strict: true`，并对每一层 object 设置 `additionalProperties: false`，同时把全部 properties 列入 `required`；业务上的可选值用包含 `null` 的类型表示。严格模式减少模型输出歧义，但不能替代本地执行前校验，因此 `ToolManager` 会再次验证类型、必填字段、额外字段和数值范围。
