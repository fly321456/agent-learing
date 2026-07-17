# L14 LLM 接口与 LLMResponse：把供应商协议翻译成 Runtime 语言

> 建议学习时间：60–90 分钟。本课只抽象一次模型调用，不抽象整次 Agent 运行。

## 1. 本节要解决的真实问题

模块 2 直接遍历 Responses API 的 `response.output`，这对学习官方协议非常必要。但如果 Runner 也到处判断 `item.type == "function_call"`、读取 `output_text`、捕获某家 SDK 的异常，那么更换模型、离线测试和协议升级都会迫使 Runtime 一起修改。

我们需要一个翻译边界：供应商适配器理解外部 SDK，把一次调用转换为内部 `LLMResponse`；Runner 只理解 content、tool_calls、continuation_items 和 finish_reason。问题不是“把任何模型都抹成完全一样”，而是隔离 Runtime 真正需要的最小共同语义。

本课的问题链是：一次模型调用和一次 Agent Run 有什么区别？Tool Call 的 call_id 在哪一层保留？为什么不能只返回字符串？为什么又不能让 Runner 读取 `raw_response.output`？供应商要求回传的原始输出项如何在不泄漏解析逻辑的前提下继续传递？

## 2. 前置回顾：模块 2 的具体协议

在 Responses API 中，一次响应可能包含文本项、推理项和一个或多个 `function_call`。应用遍历 `response.output`，执行工具，再使用相同 `call_id` 发送 `function_call_output`。这一知识没有因为抽象而消失，只是应该集中在 `OpenAILLM` 适配器中。

```text
OpenAI response.output
        ↓ provider adapter parses
LLMResponse(content, tool_calls, continuation_items)
        ↓ Runner consumes normalized fields
ToolManager / next model call
```

抽象不是假装供应商没有差异，而是指定“差异在哪一层结束”。本教学快照使用 `ScriptedLLM` 离线模拟边界，正式参考实现中的 `OpenAILLM` 才负责官方 SDK 转换。

## 3. 两个案例：为什么字符串和原始对象都不合适

案例一是纯文本回答。若 `generate()` 只返回字符串，确实够用。但第二个任务要求工具时，字符串无法可靠表达工具名、结构化参数和 call_id。把 JSON 塞进字符串又会把解析、校验和错误处理推给 Runner。

案例二是直接返回 SDK 原始对象。Runner 可以完成当前功能，却会依赖 `response.output_text`、`item.type` 和 SDK 类。离线 Fake 必须伪造整个供应商对象树；另一供应商没有相同属性时，Runner 出现大量 if/else。这不是灵活，而是依赖倒置失败。

因此我们选择内部数据模型：足够表达 Runtime 所需事实，但不承担供应商全部信息。

## 4. 概念推导：BaseLLM 是行为契约

```python
class BaseLLM(ABC):
    @abstractmethod
    def generate(
        self,
        messages: list[Any],
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        raise NotImplementedError
```

`BaseLLM` 约束的是输入和返回语义，不规定 HTTP、SDK 或模型名称。Runner 依赖这个契约，因此可使用 `ScriptedLLM` 做确定性测试，也可使用 OpenAI 适配器做真实调用。

接口越稳定越好吗？不是。过早把 streaming、音频、图像、缓存和 token usage 全塞进接口，会让初学者维护大量尚未使用字段。本课只保留 Agent Loop 必需的数据，后续需求有证据时再扩展。

## 5. 本课唯一代码增量：LLMResponse

```python
@dataclass
class LLMResponse:
    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    continuation_items: list[Any] = field(default_factory=list)
    finish_reason: str | None = None
```

`content` 是标准化文本；`tool_calls` 是 Runtime 能执行的调用；`continuation_items` 是供应商续写所需、但 Runner 不应解析的不透明项；`finish_reason` 描述这一轮模型调用为什么结束。注意它没有 events、累计 Tool Results、steps 或 run_id，因为那些属于整次 Run。

`ToolCall` 继续保留 id、name、arguments：

```python
@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]
```

call_id 是协议关联键，不是展示装饰。丢掉它会导致工具结果无法与请求配对。

## 6. 两个错误直觉与边界纠正

### 误区一：`LLMResponse` 就是 Agent 最终结果

一次 Run 可能调用模型五次。单次响应不知道前四步工具发生了什么，也不知道累计事件和总步骤。若把 `tool_results`、events 都放进 `LLMResponse`，每轮对象会重复或覆盖运行状态。整次结果应由 L16 的 `RunResult` 表达。

### 误区二：保留 `raw_response`，Runner 想用什么就用什么

这看似方便，实际绕过抽象。今天 Runner 读取 `raw_response.output`，明天测试、CLI 和 Session 都开始读取，适配层名存实亡。教学接口故意没有 `raw_response`。需要供应商续写数据时，通过 `continuation_items` 不透明转交，Runner 只负责 append，不判断内部类型。

另一个误区是抽象后不再学习官方协议。恰好相反：只有理解 provider 协议，才能正确编写适配器；抽象只是阻止这些细节扩散。

## 7. 完整运行轨迹：一次模型调用不是一次 Run

```text
messages=[user task]
ScriptedLLM.generate(...)
  → LLMResponse(
       content="",
       tool_calls=[ToolCall(call-1, read_file, {...})],
       continuation_items=[opaque provider item],
       finish_reason="tool_calls"
    )
Runner 下一步仍需执行工具并再次调用模型
```

若第二轮返回 `LLMResponse(content="done", tool_calls=[])`，才可能结束 Run。两份 `LLMResponse` 最后被一个 `RunResult` 汇总。这个一对多关系是本课必须形成的心智模型。

## 8. ScriptedLLM：为什么离线 Fake 是架构探针

源码见 [llm.py](../../../agent-from-scratch/course-checkpoints/04-runtime-refactor/src/course_runtime/llm.py)。`ScriptedLLM` 依次返回预置响应，并记录 requests：

```python
def generate(self, messages, tools=None) -> LLMResponse:
    self.requests.append({"messages": list(messages), "tools": list(tools or [])})
    response = self._responses[self._index]
    self._index += 1
    return response
```

Fake 不只是省 API 费用。它能精确构造“先 Tool Call、后文本”“永远 Tool Call”“续写项必须保留”等场景。若 Runtime 很难使用 Fake，往往说明供应商依赖泄漏得太深。

## 9. 从供应商响应到内部响应

正式适配器大致执行三步：调用 SDK；遍历输出并解析 function_call；构建内部对象。

```python
tool_calls = [
    ToolCall(item.call_id, item.name, json.loads(item.arguments))
    for item in raw_response.output
    if item.type == "function_call"
]
return LLMResponse(
    content=raw_response.output_text or "",
    tool_calls=tool_calls,
    continuation_items=list(raw_response.output),
)
```

这段代码属于 provider adapter，不属于 Runner。参数 JSON 无效时也应在适配器边界报告“模型响应无效”，而不是伪装成未知 Tool。最后核验日期：2026-07-14；具体在线实现需继续以官方 Function Calling 文档为准。

## 10. 运行命令、预期输出与故障实验

```powershell
python agent-from-scratch/course-checkpoints/04-runtime-refactor/steps/l14_llm_response.py
```

预期输出：

```text
model_call tools=1 continuation=1
```

故障实验一：把 `tool_calls` 改为空，观察这仍是合法文本响应。故障实验二：删除 ToolCall.id，尝试设计下一轮 `function_call_output`，看你还能否可靠关联。故障实验三：把不透明字典换成自定义对象，确认 ScriptedLLM 不解析它；这正是 continuation 的边界。

## 11. 基础练习与进阶挑战

基础练习：为 `ScriptedLLM` 准备两份响应，第一次请求工具，第二次返回文本，并检查 requests 数量。再画出外部 SDK 对象、`LLMResponse` 和 `RunResult` 的归属层。

进阶挑战：设计一个不破坏现有字段的 usage 数据结构，说明它为何属于单次模型调用。不要加入尚未被课程使用的十余种 provider 字段；写出“现在需要它”的验证场景后再扩展。

答案见 [模块练习参考答案](模块练习参考答案.md)。

## 12. 自测、总结与下一课

1. 为什么纯字符串不足以表达 Tool Calling？
2. `LLMResponse` 和 `RunResult` 的一对多关系是什么？
3. `continuation_items` 为什么是不透明字段？
4. Runner 为什么不允许读取 `raw_response.output`？
5. Fake LLM 除了节省费用，还能检查什么架构问题？

本课建立了模型边界，但 Tool 仍只是函数字典。下一课进入 [L15 ToolManager 与 ToolResult](L15-ToolManager与ToolResult.md)，把“模型想做什么”与“应用实际执行出什么结果”分开。

## 最终实现校准

正式 OpenAI 适配层不会只读取 `output_text`。它先解析 function call，再识别 refusal 内容块，并把 `incomplete`、`failed`、`cancelled` 分别映射为显式 `finish_reason` 和 `status_detail`；同步调用若仍是 `queued` 或 `in_progress` 会被拒绝，未知状态也不会默认为成功。这样 Runner、CLI 与测试不必了解 SDK 对象，但仍能区分“正常完成”“模型拒绝”和“供应商未完成”。依据见 [Responses create 官方参考](https://developers.openai.com/api/reference/resources/responses/methods/create)。
