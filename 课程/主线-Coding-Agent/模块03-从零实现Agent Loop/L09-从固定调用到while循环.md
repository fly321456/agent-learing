# L09 从固定两次调用到 while Loop：让响应决定下一步

> 建议学习时间：60–90 分钟。本课完全离线，先把 L08 的固定往返改成最小通用循环。

## 1. 本节要解决的真实问题

L08 固定执行“模型调用 1 → Tool → 模型调用 2”。如果第二次响应再次请求 Tool，代码只能复制第三次调用；任务需要几轮未知时，复制次数永远不够。我们需要让程序根据当前 Response 决定：有 Tool Call 就执行并继续，没有 Tool Call 就结束。

本课只引入一个核心概念：**Agent Loop 的轮数由运行中的响应决定，而不是由开发者提前写死。** `while` 或 `for` 是实现手段，反馈数据流才是本质。

## 2. 前置知识与问题链

模块 2 已能保留原始 Function Call、执行 Python 并追加 Function Call Output。继续追问：第二次仍请求工具怎么办？模型永远请求工具怎么办？工具结果存在哪里？何时能把文本当最终答案？

```text
固定往返：request1 → tool → request2 → return
通用循环：request → inspect → tool/finish → request again
```

由此得到循环的三个职责：维护 input items；判断 response 中是否有 Tool Call；强制最大步骤。

## 3. 类比：医生不是固定问两句话

问诊不会规定“医生只能问两次”。医生根据上一个检查结果决定继续检查还是给出结论。但医院仍会限制检查范围、费用和时间。Agent 也是如此：模型动态决定下一步，Runtime 用 `max_steps` 控制资源。

案例一“计算 6×7”可能一轮 Tool、第二轮完成。案例二“分析仓库入口”可能先列文件、再读配置、再搜索函数，轮数由 Observation 决定。

## 4. 修改前后的控制流

```python
# before: 路径固定
first = model.generate(items)
execute(first.tool_calls)
second = model.generate(items)
return second.content
```

```python
# after: 响应控制路径
for step in range(1, max_steps + 1):
    response = model.generate(items, tools)
    if not response.tool_calls:
        return completed(response.content)
    execute_and_append(response.tool_calls)
return max_steps_result()
```

循环没有让模型直接控制程序。模型只能在宿主提供的工具和步数边界内请求行动。

## 5. 本课核心：继续条件与完成条件

本课程约定：`tool_calls` 非空表示需要行动；为空表示模型给出最终文本。Runtime 不根据 content 是否为空猜测，也不把一次 Tool 成功当成整次 Run 完成。

每轮必须把 Tool Call 与 Tool Result 追加到 `items`。如果每轮重新创建 items，模型会忘记刚才发生什么，只能重复请求同一工具。

## 6. 两个错误直觉与纠正

### 误区一：加一个 `while True` 就是 Agent

如果循环每轮执行固定函数，或 Observation 不回传，它只是重复器。闭环要求新结果改变后续模型输入。

### 误区二：模型会自己停止，不需要上限

模型可能重复工具、遇到不充分结果或脚本 Fake 永远返回同一响应。`max_steps` 必须由程序强制。

### 误区三：Tool 成功就可以 break

成功只代表行动完成。最终回答需要下一次模型响应，多个行动也可能尚未完成目标。

## 7. 完整运行轨迹

```text
Task: ping once
Step 1 ModelResponse: tool_calls=[ping]
Step 1 Action: ping()
Step 1 Observation: pong
Step 2 ModelResponse: content=done, tool_calls=[]
Finish: completed, steps=2, answer=done
```

若第二轮仍返回 ping，循环会继续，直到出现无 Tool Call 的响应或达到 `max_steps`。

## 8. 完整递增代码

源码位于 [l09_while_loop.py](../../../agent-from-scratch/course-checkpoints/03-agent-loop/steps/l09_while_loop.py)，核心实现位于 [agent_loop.py](../../../agent-from-scratch/course-checkpoints/03-agent-loop/agent_loop.py)。

```python
def run_agent(task, model, tools, max_steps=5):
    items = [{"role": "user", "content": task}]
    results = []
    trace = []
    for step in range(1, max_steps + 1):
        response = model.generate(items, list(tools))
        trace.append({"step": step, "tool_calls": len(response.tool_calls),
                      "content": response.content})
        if not response.tool_calls:
            return {"answer": response.content, "tool_results": results,
                    "trace": trace, "steps": step,
                    "finish_reason": "completed"}
        for call in response.tool_calls:
            result = execute_tool(call, tools)
            results.append(result)
            items.append({"type": "function_call", "call_id": call.id,
                          "name": call.name, "arguments": call.arguments})
            items.append({"type": "function_call_output",
                          "call_id": call.id, "output": result})
    return {"answer": "", "tool_results": results, "trace": trace,
            "steps": max_steps, "finish_reason": "max_steps"}
```

## 9. 逐段解释

`items` 活在循环外，保证历史累积。`range(1, max_steps + 1)` 同时提供步骤号和硬上限。Trace 记录每轮响应摘要，便于判断为什么继续。完成分支与耗尽分支都返回同一种字典形状，调用者不必猜测。

当前 `ScriptedModel` 只返回预设响应，是 Fake LLM。它记录每次收到的 items，使测试可以证明第二轮看到了第一轮 Observation。

## 10. 运行与故障实验

```powershell
python agent-from-scratch/course-checkpoints/03-agent-loop/steps/l09_while_loop.py
```

预期：`steps=2 finish_reason=completed`。故障实验一：把 items 初始化移入循环，检查第二轮请求丢失历史。实验二：让 Fake 重复最后 Tool Response，设置 `max_steps=2`，确认停止。实验三：第一轮直接返回文本，确认 Tool 不执行且 steps 为 1。

## 11. 基础练习与进阶挑战

基础练习：打印每轮 items 长度，解释增长原因。第二项练习：用三轮脚本实现“列文件 → 读 README → 完成”。进阶挑战：增加 `on_step` 回调实时输出 Trace，但不得改变累计结果。

答案见 [模块练习参考答案](模块练习参考答案.md)。

## 12. 自测、总结与下一课

1. 固定两次调用遇到第三次 Tool Request 会怎样？
2. 为什么 items 必须定义在循环外？
3. 无 Tool Call 为什么可以作为完成条件？
4. `max_steps` 为什么不能只写在 Prompt 中？
5. `for` 循环与 Agent Loop 的本质区别是什么？

本课完成通用循环骨架，但工具执行仍需要通用路由。下一课 [L10 Tool Registry 与通用路由](L10-Tool Registry与通用路由.md) 将把名称查找、参数传递和结果结构集中起来。
