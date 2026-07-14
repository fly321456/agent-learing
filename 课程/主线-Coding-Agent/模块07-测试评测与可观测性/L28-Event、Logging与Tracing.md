# L28 Event、Logging 与 Tracing：让失败从“模型不行”变成可定位事实

> 建议学习时间：60–90 分钟。本课完成模块 7，将 Event 以 UTF-8 JSONL 形式保存。

## 1. 本节要解决的真实问题

评测告诉我们 1 条任务失败，却不告诉失败发生在哪一步。工程师若只能看到最终空字符串，常会猜“模型变笨了”；真实原因可能是 Context 裁掉 Tool Result、call_id 错配、审批拒绝或 Retry 耗尽。

Observability（可观测性）要求 Runtime 把内部执行转换为外部可查询事实。Event 是结构化事实，Logging 是面向人和系统的记录，Tracing 是按 run_id/sequence 还原整条链路。本课不引入复杂平台，先用一行一个 JSON 的 JSONL Trace。

问题链是：print 与 Event 有何区别？为什么 JSONL 比一个巨大 JSON 数组更适合追加？Trace 是否应包含完整敏感参数？Event Sink 失败应否影响 Run？如何从 sequence 定位缺失事件？

## 2. 三个术语的边界

Event：Runtime 中发生的结构化事实，例如 tool_called。Logging：把事实和诊断写到终端、文件或服务。Tracing：用 run_id 将多个 Event 关联，并保留父子/顺序关系。

```text
Runner emit Event
  ├─ accumulate in RunResult
  ├─ CLI render human text
  └─ JsonlTraceWriter persist machine-readable record
```

不要在 Runner 中散落 print。相同 Event 可由不同消费者展示，核心协议保持界面无关。

## 3. Event 契约回顾

```python
@dataclass(frozen=True)
class Event:
    type: str
    sequence: int
    run_id: str
    step: int
    data: dict[str, Any]
```

type 用于分类；sequence 恢复全序；run_id 关联一次运行；step 对应模型轮次；data 保存类型特有字段。时间戳很有用，但教学脚本省略以保持完全确定；正式 Runtime 已加入 UTC timestamp。

Event type 应稳定，data 可演进。若下游依赖任意自然语言日志，改一个句子就会破坏解析。

## 4. 类比与两个调试案例

Event Trace 像飞机黑匣子，不决定飞机怎么飞，却让事故后能重建顺序。

案例一：Trace 有 llm_completed(tool_call_count=1)，随后缺少 tool_called，说明 Runner 在模型与 ToolManager 之间中断。案例二：tool_completed(status=denied) 后又出现第二次同 call_id 的 tool_called，说明拒绝策略或恢复去重错误。

第三个案例：sequence 为 1、2、4，契约测试立即指出事件丢失；仅靠时间戳排序可能因相同时间和时钟误差不稳定。

## 5. 本课唯一代码增量：JsonlTraceWriter

```python
class JsonlTraceWriter:
    def __call__(self, event):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(asdict(event), ensure_ascii=False) + "\n")
```

Callable 对象可直接作为 event_sink。每次 append 一行，进程中断最多影响最后一条；消费者可流式逐行读取，不必加载整个数组。`ensure_ascii=False` 让中文 Tool 输出可读，文件严格 UTF-8。

## 6. Event Contract 验证

```python
if [event.sequence for event in events] != list(range(1, len(events) + 1)):
    raise ValueError("event sequence must be continuous from 1")
if len({event.run_id for event in events}) != 1:
    raise ValueError("all events must share one run_id")
```

这两个不变量不是完整 Trace 语法，却能捕获最常见的累计/串 Run 问题。进阶契约还可要求首项 run_started、末项 run_completed，以及 tool_called/tool_completed 按 call_id 配对。

## 7. 两个错误直觉与纠正

### 误区一：日志越详细越容易排错

无限记录 prompts、源码、环境变量和 Tool 输出会泄露秘密、增加成本并制造噪声。应按字段白名单、截断和脱敏，安全优先于“以后也许有用”。

### 误区二：有 Trace 就不需要 RunResult

Trace 是事件流，调用者常需要直接读取 content、finish_reason 和 Tool Results。RunResult 是稳定聚合视图，Trace 是诊断细节，两者互补。

另一个误区是 Trace Writer 失败后静默丢失。展示型 sink 可以记录 sink failure 后继续；合规审计型 sink 可能必须 fail closed。策略应显式配置。

## 8. 完整 JSONL 轨迹

```json
{"type":"run_started","sequence":1,"run_id":"run-1","step":0,"data":{}}
{"type":"tool_completed","sequence":2,"run_id":"run-1","step":1,"data":{"status":"success"}}
{"type":"run_completed","sequence":3,"run_id":"run-1","step":1,"data":{"finish_reason":"completed"}}
```

每行独立 JSON。读取后验证 sequence=[1,2,3]、type 顺序一致、run_id 唯一。若 data 中含大型 stdout，应在 Event 产生前截断并记录 `truncated=true`。

## 9. 从单 Run Trace 到评测分析

L27 的失败分类指出哪类任务退化，L28 的 Trace 解释具体为什么。两层形成诊断漏斗：

```text
dashboard: safety success rate dropped
  → failed case safety-04
  → run_id trace
  → run_command timeout after approval
  → inspect command timeout/config
```

没有聚合指标，工程师不知道先看哪个 Run；没有 Trace，指标只是一串数字。

## 10. 运行、预期输出与故障实验

```powershell
python agent-from-scratch/course-checkpoints/07-testing-evaluation/steps/l28_jsonl_trace.py
cd agent-from-scratch
python -m pytest -q tests/test_course_module7.py
```

```text
events=2 sequences=[1, 2]
```

故障实验：制造 sequence 缺口；混入第二个 run_id；写入中文 data 检查编码；中途写一行非法 JSON 模拟损坏；将大型输出截断；让 Trace 路径不可写并设计 sink 策略。

## 11. 基础练习与进阶挑战

基础练习：按 type 统计 Event 数量，并从 JSONL 找到最终 finish_reason。进阶挑战：实现 `validate_tool_pairs`，保证每个 tool_called 最多有一个同 call_id 的 tool_completed，并处理 denied/timeout。

答案见 [模块练习参考答案](模块练习参考答案.md)。

## 12. 自测、总结与下一模块

1. Event、Logging、Tracing 分别是什么？
2. JSONL 为什么适合追加与流式读取？
3. sequence 与 timestamp 的作用有何不同？
4. 为什么 Trace 不能无限记录原始数据？
5. 聚合评测与单 Run Trace 如何配合？

模块 7 已让 Runtime 的正确性、回归和失败都可验证。下一模块从 [L29 CLI 事件展示与人工审批](../模块08-CLI-MCP与作品化/L29-CLI事件展示与人工审批.md) 开始，把这些能力交付成可使用的作品。
