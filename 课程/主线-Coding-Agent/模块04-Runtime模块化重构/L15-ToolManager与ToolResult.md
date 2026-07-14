# L15 ToolManager 与 ToolResult：把“请求行动”变成“可解释观察”

> 建议学习时间：60–90 分钟。本课只建立通用工具执行边界；文件安全、审批和超时在模块 5 增加。

## 1. 本节要解决的真实问题

模块 3 的 Tool Registry 已经能用名称找到函数，但正式 Runtime 还需要回答更多问题：给模型看的 Schema 从哪里来？处理器和描述如何保持一致？未知 Tool 是抛异常还是返回 Observation？Python 函数返回整数、路径或对象时，下一轮模型究竟收到什么？同一轮两个同名调用如何区分？

这些问题都指向一个边界：`ToolManager` 负责注册、导出 Schema、路由和标准化执行；`ToolResult` 负责表达一次实际行动结果。LLM 提出的 `ToolCall` 只是请求，不代表工具已经成功，更不代表整个 Agent Run 已完成。

问题链是：模型能否直接持有 Python 函数？Schema 和 handler 名称不一致会怎样？工具异常为什么不应直接摧毁整个 Loop？错误若只变成字符串，调用者还能区分 unknown 与业务失败吗？

## 2. 前置回顾：从字典 Registry 到 ToolSpec

模块 3 使用：

```python
TOOLS = {"calculator": calculate, "current_time": current_time}
```

它已经解决通用路由，却没有保存 description 与 parameters。模型需要 Schema 决定何时调用和怎样生成参数，Python 需要 handler 真正执行。若两份配置分散维护，改名时很容易出现模型看到 `read_file`，Registry 却只注册 `read_text`。

因此把“给模型看的声明”和“给 Python 用的实现”收进同一个 `ToolSpec`。Spec 是工具能力的静态说明；Result 是某次执行的动态事实，两者生命周期不同。

## 3. 一致类比与两个实际案例

把 ToolSpec 想成工具柜标签：名称、用途、输入规格以及柜中真正的工具。ToolCall 是领用单，ToolManager 是管理员，ToolResult 是带工单号的执行回执。领用单写了“螺丝刀”不代表螺丝已拧好；管理员还可能发现不存在该工具或执行中损坏。

案例一：模型调用 `echo(text="hello")`。Manager 找到处理器，返回 `ToolResult(call_id="c1", status="success", output="hello")`。案例二：模型调用 `delete_database`，Registry 中没有它。Manager 返回 error Observation，下一轮模型可以说明能力不足或改选工具，Python 进程无需因 KeyError 崩溃。

第三个边界案例是同轮两次 `read_file`。它们 name 相同，但 call_id 不同。结果必须按 call_id 关联，不能以 name 为字典键覆盖第一项。

## 4. ToolSpec：声明与处理器的单一来源

```python
@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]
    handler: ToolHandler

    def as_schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }
```

`handler` 不发给模型，`as_schema()` 只输出协议所需字段。这样既不暴露可执行对象，也避免手写第二份名称。模块 5 会再加入 risk 和工作区 Context，但本课不提前塞入权限系统。

好的 Tool description 应说明结果和边界，而非重复名称；parameters 应尽量小且明确。ToolManager 不能靠 Prompt 修复含糊接口，工具本身必须对模型友好。

## 5. 本课唯一代码增量：统一 execute

```python
class ToolManager:
    def execute(self, call: ToolCall) -> ToolResult:
        tool = self._tools.get(call.name)
        if tool is None:
            return ToolResult(
                call.id, call.name, "error", error=f"Unknown tool: {call.name}"
            )
        try:
            output = tool.handler(**call.arguments)
        except Exception as exc:
            return ToolResult(call.id, call.name, "error", error=str(exc))
        return ToolResult(call.id, call.name, "success", output=str(output))
```

Runner 以后只调用这一入口，不自己查 Registry、不自己捕获每种 Tool 异常。统一入口还为下一模块加入审批、耗时和 Timeout 提供唯一扩展点。

## 6. ToolResult 的语义边界

```python
@dataclass(frozen=True)
class ToolResult:
    call_id: str
    name: str
    status: ToolStatus
    output: str = ""
    error: str | None = None
```

`call_id` 关联请求；`name` 方便人类调试；`status` 供程序稳定分支；`output` 是成功观察；`error` 是失败说明。不要要求调用者解析 `"ERROR: ..."` 前缀来判断状态，因为文本格式一改，控制流就会坏。

ToolResult 不包含 Agent 最终答案，也不决定 `finish_reason`。一个工具失败后模型可能换方法并完成；所有工具成功后模型仍可能无限循环。因此 Tool status 与 Run finish reason 必须是两套概念。

## 7. 两个错误直觉与失败边界

### 误区一：工具失败就直接 raise 到应用顶层

未知 Tool、参数不匹配或文件不存在，有些是模型可恢复的 Observation。若全部抛出，模型没有重新决策机会。ToolManager 应将预期执行失败标准化；真正的进程级错误是否继续，则由更高层策略决定。

### 误区二：捕获 `Exception` 后返回空字符串最稳

空字符串会制造假成功。模型不知道是文件为空、工具不存在还是执行失败，测试也无法定位责任。本课保留 status 和 error。模块 5 会把 denied 与 timeout 进一步分开，因为它们需要不同恢复方式。

另一个误区是 ToolManager 自动修改模型参数，例如猜测错别字或填默认路径。这会让 Trace 隐藏真实决策。Manager 应校验和执行，不应偷偷重写意图。

## 8. 完整轨迹：成功、未知与处理器异常

```text
ToolCall(c1, echo, {text: hello})
  → lookup echo
  → handler returns hello
  → ToolResult(c1, echo, success, output=hello)

ToolCall(c2, missing, {})
  → lookup fails
  → ToolResult(c2, missing, error, error="Unknown tool: missing")

ToolCall(c3, broken, {})
  → handler raises RuntimeError("boom")
  → ToolResult(c3, broken, error, error="boom")
```

三条路径都返回相同类型，Runner 因而可以统一记录事件并构造下一轮 Observation。

## 9. 关键实现与不变量

源码见 [tools.py](../../../agent-from-scratch/course-checkpoints/04-runtime-refactor/src/course_runtime/tools.py)。构造函数先检查名称唯一：

```python
self._tools = {tool.name: tool for tool in tools}
if len(self._tools) != len(tools):
    raise ValueError("Tool names must be unique")
```

如果允许重名，字典会静默保留最后一个处理器，模型看到的 Schema 顺序与实际执行可能不一致。启动时拒绝比运行中猜测安全。

当前 handler 返回值统一 `str()`，是教学版最小协议。生产系统可能需要结构化 output，但也应定义可序列化边界，不能把任意 Python 对象直接传给 SDK。

## 10. 运行命令、预期输出与故障实验

```powershell
python agent-from-scratch/course-checkpoints/04-runtime-refactor/steps/l15_tool_manager.py
```

预期输出：

```text
success=success:observed unknown=error:Unknown tool: missing
```

故障实验一：注册两个同名 ToolSpec，确认初始化立即失败。故障实验二：让 echo 缺少 text 参数，观察 TypeError 被转成 error Result。故障实验三：把异常分支改为空字符串，比较 Trace 是否还能解释失败。故障实验四：同轮执行两个同名不同 call_id 的请求，确认结果没有覆盖。

## 11. 基础练习与进阶挑战

基础练习：加入 `uppercase(text)` ToolSpec，并分别执行成功和缺参调用。打印 schemas，确认 handler 没有泄漏给模型。再为 ToolResult 写一个格式化函数，明确输出 status、call_id 和错误。

进阶挑战：设计 `invalid_arguments` 是否应作为独立状态。讨论它与 handler 内部业务 ValueError 如何区分；不要只增加枚举值，还要说明在哪一层校验以及模型下一轮能采取什么动作。

答案见 [模块练习参考答案](模块练习参考答案.md)。

## 12. 自测、总结与下一课

1. ToolCall 与 ToolResult 为什么不是同一个对象？
2. ToolSpec 为什么同时保存 Schema 信息和 handler？
3. 同名两次调用为什么必须靠 call_id 关联？
4. Tool error 为什么不自动等于 Run error？
5. 返回空字符串为什么会制造不可解释的假成功？

本课已经让每次行动有稳定回执。下一课 [L16 Runner、RunResult 与 Event](L16-Runner、RunResult与Event.md) 会把 Agent、LLM 和 ToolManager 重新接成完整闭环，并证明事件属于整次 Run。
