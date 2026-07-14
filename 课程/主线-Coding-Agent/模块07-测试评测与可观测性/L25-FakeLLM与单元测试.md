# L25 FakeLLM 与单元测试：把不确定模型换成确定协议剧本

> 建议学习时间：60–90 分钟。本课聚焦小型、快速、离线测试，不把网络 Mock 当成 Agent 测试的全部。

## 1. 本节要解决的真实问题

用真实 LLM 测 Runner 会受到模型更新、采样、网络、限流和费用影响。同一个 commit 今天通过、明天可能选择不同 Tool。若因此只手工聊天，Loop 的未知 Tool、max_steps 和 Retry 分支就没有回归保护。

FakeLLM（伪模型）不是模拟“智能”，而是提供确定的协议剧本：第一次返回 Tool Call，第二次返回文本；或连续返回调用；或抛 RetryableError。它让我们测试自己的 Runtime，而不是测试供应商模型是否始终说同一句话。

问题链是：Fake 与 Mock 有何区别？预置响应耗尽应重复最后一项还是失败？为何要记录 requests？测试应断言内部方法调用，还是最终 Result 与下一轮输入？

## 2. 测试边界：我们拥有哪部分代码

```text
供应商 SDK / 模型行为：不在单元测试中证明
Provider adapter：用固定供应商形状做契约测试
Runner 状态机：用 FakeLLM 证明
Tool handler：用真实临时文件和纯函数证明
```

单元测试的价值来自边界清楚。若 Fake 必须伪造几十层 SDK 私有对象，说明 LLMResponse 抽象泄漏；若测试只能搜索 stdout，说明 RunResult 不够结构化。

## 3. 类比与两个案例

FakeLLM 像飞行模拟器中的预设天气，不声称复刻整个天空，只稳定触发“引擎警报后如何处理”的流程。

案例一：responses 为 `first`、`second`。两次 generate 应按序返回，并保存两份输入快照。案例二：先返回 `ToolCall(read_file)`，再返回最终文本，测试断言第二次 request 同时包含 continuation item 和相同 call_id 的 function_call_output。后者测试的是协议链，而不是模型语言质量。

失败案例：Fake 响应耗尽时立即抛错，提醒测试剧本不完整。默认重复最后一项会把遗漏隐藏成无限 Loop；只有专门测试 max_steps 时才显式 repeat_last。

## 4. Fake、Stub 与 Mock

Stub 只返回固定值；Fake 实现一个可用但简化的依赖，例如按序响应并记录请求；Mock 常用于验证某方法被调用几次。课程偏好 Fake 和结果断言，因为过度 Mock 会把测试绑定到实现顺序。

```python
fake = FakeLLM([{"content": "first"}, {"content": "second"}])
assert fake.generate(messages)["content"] == "first"
assert fake.generate(messages)["content"] == "second"
```

我们关心返回内容、请求快照和 Runtime 终态，而不是 Runner 内部私有函数名。

## 5. 本课唯一代码增量：可记录 FakeLLM

```python
class FakeLLM:
    def generate(self, messages, tools=None):
        self.requests.append({
            "messages": list(messages),
            "tools": list(tools or []),
        })
        if self._index >= len(self._responses):
            raise RuntimeError("FakeLLM has no response left")
        response = self._responses[self._index]
        self._index += 1
        return response
```

`list(messages)` 复制容器快照，避免 Runner 后续 append 让旧 request 看起来也发生变化。若元素本身会原地修改，则需要更深复制或不可变消息；课程 Runtime 采用追加而非修改已有 item。

## 6. 应优先覆盖的状态机分支

最小 Agent Loop 至少测试：直接文本完成；一次 Tool；同轮多 Tool；未知 Tool；非法参数；Tool exception；审批拒绝；max_steps；Retryable 恢复；Deterministic 立即失败。

```text
input → scripted response → runtime action → structured result
```

每个测试聚焦一个行为，失败时才能知道是哪条协议退化。把所有路径塞进一个“完整 Agent works”测试，出错后定位成本很高。

## 7. 两个错误直觉与纠正

### 误区一：Fake 测试通过就代表真实 Agent 效果好

Fake 只证明给定 Tool 序列时 Runtime 正确，不证明真实模型会选择该序列。模型选择质量要靠 L27 的在线或录制评测，不能用 20/20 协议回放冒充智能成功率。

### 误区二：测试请求必须与完整 list 精确相等

过度精确会让新增合法 system item 导致无关失败。应断言关键不变量：call_id 对齐、Tool output 存在、Instructions 在正确角色、事件顺序连续。

另一个误区是 Fake 永不抛错。没有错误剧本，Retry 和 Run error 永远未经证明。

## 8. 完整测试轨迹

```text
Arrange: FakeLLM([tool_response, final_response])
Act: Runner.run(agent, task)
Step 1: Fake returns ToolCall c1
ToolManager returns ToolResult c1
Step 2: Fake request contains provider item + function_call_output c1
Fake returns final text
Assert: finish_reason=completed, steps=2, tool_results=1
```

这种 Arrange–Act–Assert 轨迹可直接映射 Agent Loop，不需要联网即可稳定复现。

## 9. 测试可读性与 DAMP

测试代码允许适度重复，使每个场景独立可读。一个名为 `test_runner_stops_at_max_steps_after_repeated_tool_calls` 的测试，比 `test_case_7` 或十层 fixture 更像规范。

```python
assert result.finish_reason == "max_steps"
assert result.steps == 2
assert len(result.tool_results) == 2
```

断言结果状态，不断言 `_run_loop` 调了 `_generate` 两次。前者允许内部重构，后者把实现细节冻结。

## 10. 运行、预期输出与故障实验

```powershell
python agent-from-scratch/course-checkpoints/07-testing-evaluation/steps/l25_fake_llm.py
```

```text
responses=first,second requests=2
```

故障实验：请求第三次响应确认明确失败；不复制 messages 后继续 append，观察旧 request 被污染的条件；交换两份响应观察状态机变化；让 Fake 抛暂时性与确定性错误比较调用数。

## 11. 基础练习与进阶挑战

基础练习：编写先 Tool 后文本的 Fake 剧本，并检查第二次请求。进阶挑战：为 Fake 增加 callable response，使它能根据输入生成结果，但保持确定性；说明何时 callable 会让测试重新变复杂。

答案见 [模块练习参考答案](模块练习参考答案.md)。

## 12. 自测、总结与下一课

1. FakeLLM 测试证明什么、不能证明什么？
2. 为什么要记录请求快照？
3. 响应耗尽为什么默认应失败？
4. 结果断言为何优于私有方法调用断言？
5. 哪些 Agent Loop 分支必须离线覆盖？

下一课 [L26 契约、集成与 E2E](L26-契约、集成与E2E.md) 将从单组件扩展到真实临时 Git 仓库，检查组件连接处。
