# L06 第一次 Responses API 文本调用：先分清 API 与模型

> 建议学习时间：60–90 分钟。离线实验必修，真实 API 选做且必须显式添加 `--online`。

## 1. 本节要解决的真实问题

L05 已经能构造请求，但还没有“发送—接收”。初学者第一次调用 API 时，常把 SDK、HTTP API、模型和 Agent 混成一件事：程序报认证错误就说模型不会回答；拿到一段文本就说 Agent 已完成；看到 `output_text` 就以为响应只有字符串。

本课只完成一次文本调用。我们要理解 `client.responses.create(...)` 是边界调用，模型名称由运行配置提供，`response.output_text` 是 SDK 提供的便利聚合，而完整 `response.output` 仍可能包含多种项目。Tool Calling 留到下一课。

为了让必修路径稳定，本课先用 `ScriptedResponsesClient` 模拟相同调用形状。只有显式使用 `--online` 且环境同时存在 `OPENAI_API_KEY`、`OPENAI_MODEL` 时才访问网络。

## 2. 前置回顾与问题链

```text
Python request dict
    ↓ client.responses.create
Responses API
    ↓ model processes current context
Response object
    ↓ output_text / output
Application
```

API 负责接收请求和返回协议对象；模型负责根据输入生成输出；SDK 把 HTTP 细节包装成 Python 方法；应用负责配置、错误处理和后续行为。它们职责不同。

继续追问：模型名应该写死吗？密钥应放进源码吗？在线调用失败是否会破坏离线学习？一次文本回答是否形成 Agent Loop？答案分别是“不应该”“不应该”“不应该”“没有”。

## 3. 类比与两个具体案例

把 Responses API 想成快递柜台：Request 是包裹和地址，SDK 是下单界面，模型是处理包裹的服务，Response 是回执。界面崩溃不代表服务不会处理，地址不存在也不是包裹内容错误。

案例一是概念问答：“Observation 是什么？”一次文本调用足够，因为所有必要信息都在问题中。案例二是“当前仓库测试是否通过？”单次文本调用不够，因为模型没有运行测试。即使它生成“测试通过”，也没有 Observation 证据。

这两个案例提醒我们：Responses API 是模型能力入口，不自动提供环境行动。Agent 要到后续课程把模型调用、工具执行和循环连接起来。

## 4. 离线客户端为什么不是假装调用 API

测试替身的目标不是模拟模型智能，而是固定协议行为。`ScriptedResponsesClient.create(**request)` 记录请求并返回预设 `ScriptedResponse`。这样可以断言 instructions 与 input 是否正确，不受网络、费用、限流和模型随机性影响。

```python
client = ScriptedResponsesClient([
    ScriptedResponse(output_text="An Observation is the recorded result of an action.")
])
answer = generate_text(
    client,
    "course-model",
    "Answer with one precise sentence.",
    "What is an Observation?",
)
```

离线 Fake 验证应用协议；在线实验验证真实集成。两者互补，不能用一次在线成功代替自动测试。

## 5. 本课核心概念：一次模型调用的边界

`generate_text` 接收 client、model、instructions 和 user input，调用一次 `create`，返回 `output_text`。它不保存 Session、不调用 Tool、不重试、不循环。这种刻意限制让我们能准确回答“这一课新增了什么”。

真实响应的 `output_text` 是便利属性。后续 Tool Calling 必须遍历 `response.output`，因为 function call 不等于普通文本。现在先使用文本便利属性，但不要把它当成完整协议。

## 6. 两个错误直觉与纠正

### 误区一：API 调用成功就有了 Agent

一次请求仍是 Single-shot LLM。Agent Loop 需要在模型请求 Tool 后执行行动、追加 Observation 并再次调用。

### 误区二：把 API Key 写入脚本最方便

密钥会进入版本历史、日志或截图。SDK 默认可从环境读取。课程只检查变量是否存在，绝不打印密钥。

### 误区三：在线结果比离线测试更可信

在线结果证明某次集成可用，却可能随模型、网络变化。离线测试证明请求结构和应用分支稳定。默认验收必须离线。

## 7. 完整运行轨迹

```text
mode: offline
request.model: course-model
request.instructions: Answer with one precise sentence.
request.input: What is an Observation?
response.output_text: An Observation is the recorded result of an action.
network_calls: 0
```

在线选做轨迹只保证出现 `mode: online` 与非空 `output_text`，不把自然语言逐字写进断言。

## 8. 完整代码

核心函数位于 [responses_core.py](../../../agent-from-scratch/course-checkpoints/02-tool-calling/responses_core.py)，运行入口位于 [l06_first_responses_text_call.py](../../../agent-from-scratch/course-checkpoints/02-tool-calling/steps/l06_first_responses_text_call.py)。

```python
def generate_text(client, model, instructions, user_input):
    response = client.create(
        model=model,
        instructions=instructions,
        input=user_input,
    )
    return response.output_text
```

真实调用只在在线分支出现：

```python
api_key = os.getenv("OPENAI_API_KEY")
model = os.getenv("OPENAI_MODEL")
if not api_key or not model:
    raise SystemExit("Online mode requires OPENAI_API_KEY and OPENAI_MODEL")
response = OpenAI(api_key=api_key).responses.create(
    model=model,
    instructions="Answer with one precise sentence.",
    input="What is an Observation in an agent loop?",
)
print(response.output_text)
```

## 9. 逐段解释与错误定位

依赖注入 `client` 让同一函数既可接受 Scripted Client，也可接受兼容的真实边界封装。`model` 由外部传入，课程不会声明某个名称永久正确。`output_text` 只用于文本结果，下一课将检查 `output` 项。

认证失败检查环境变量；模型不存在检查 `OPENAI_MODEL`；连接失败属于网络层；响应解析失败属于协议层。不要用一个宽泛 `except Exception: return "failed"` 抹掉根因。

## 10. 运行与故障实验

```powershell
python agent-from-scratch/course-checkpoints/02-tool-calling/steps/l06_first_responses_text_call.py
```

选做在线实验：

```powershell
python agent-from-scratch/course-checkpoints/02-tool-calling/steps/l06_first_responses_text_call.py --online
```

故障实验：删除 Scripted Response，确认客户端明确报告“no response left”；在没有环境变量时运行 `--online`，确认程序在发请求前停止；把 `output_text` 设为空字符串，思考“调用成功”和“有可用答案”为何不同。

## 11. 练习与挑战

基础练习：断言 Fake 记录的请求恰好包含 model、instructions、input。第二项练习：给在线分支增加超时错误提示，但不要自动无限重试。进阶挑战：打印 `response.output` 的项目类型，不依赖具体文本内容。

答案见 [模块练习参考答案](模块练习参考答案.md)。

## 12. 自测与下一课

1. SDK、Responses API 和模型分别负责什么？
2. 为什么默认测试不能依赖真实 API？
3. `output_text` 与 `response.output` 有什么区别？
4. 一次文本调用为什么还不是 Agent？
5. 为什么模型名称与密钥都不应硬编码？

下一课 [L07 Tool Schema 与 function_call](L07-Tool Schema与function_call.md) 将让模型不再直接回答时间，而是返回一个结构化行动请求。

## 官方核验

- 最后核验日期：2026-07-14
- [OpenAI Text generation](https://developers.openai.com/api/docs/guides/text)
