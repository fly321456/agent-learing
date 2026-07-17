# L23 Checkpoint 与恢复：恢复不是重跑，副作用不能执行两次

> 建议学习时间：60–90 分钟。本课实现最小检查点，并用 call_id 证明副作用去重。

## 1. 本节要解决的真实问题

Agent 在应用补丁后、写入下一轮模型请求前进程崩溃。重启后若从头执行，Patch 可能再次运行；命令可能重复发布、重复删除或重复扣费。若直接跳到下一步，又需要知道上次到底成功到哪里、哪个 Tool Result 已产生。

Checkpoint（检查点）不是“保存几条消息”这么简单，而是一个恢复协议：记录 run_id、下一步、已完成副作用及其结果；恢复时复用相同身份，避免对同一 call_id 重复执行。问题链是：何时保存？先执行还是先标记完成？写文件中断怎么办？失败 Tool 要不要缓存？call_id 是否足以保证幂等？

## 2. Session 与 Checkpoint 的区别

```text
Session: 用户与 Agent 的长期对话，完成后仍保留
Checkpoint: 某个 Run 的中间执行状态，服务崩溃恢复
```

Session 中“我已经修改文件”只是文本，不能作为副作用完成证据；Checkpoint 中 call_id 对应的 Tool Result 才是执行状态。反过来，Checkpoint 不应代替长期会话，它可能在 Run 完成后清理。

## 3. 类比与两个失败窗口

Checkpoint 像物流系统的扫描记录。包裹已装车后系统重启，不能因为页面刷新再装一次；应查询运单号是否完成该动作。

失败窗口一：先执行 Tool，再保存 Checkpoint，中间崩溃。外部副作用已发生但记录缺失，恢复会重复。失败窗口二：先写“完成”，再执行 Tool，中间崩溃。记录声称成功，实际没有发生。单机 JSON 无法完全消除这两个窗口，它只能教学“至少在可控范围用稳定 call_id 去重”。真正跨系统 exactly-once 需要 Tool 自身幂等键或事务支持。

## 4. 最小 Checkpoint 数据模型

```python
@dataclass
class RunCheckpoint:
    run_id: str
    next_step: int
    completed_calls: dict[str, str] = field(default_factory=dict)
```

run_id 关联原运行；next_step 告诉 Runner 从哪轮继续；completed_calls 把 call_id 映射到已产生 output。教学版只存字符串，正式 Runtime 应保存完整 ToolResult、input_items 和 Event。

为什么键是 call_id 而非 Tool 名？同一个 Run 可能两次调用 apply_patch，名称相同但意图不同；call_id 才对应协议中的单次请求。

## 5. 本课唯一代码增量：execute_once

```python
def execute_once(checkpoint, call_id, operation):
    if call_id in checkpoint.completed_calls:
        return checkpoint.completed_calls[call_id]
    output = operation()
    checkpoint.completed_calls[call_id] = output
    return output
```

第一次执行并记录；恢复后相同 call_id 直接返回旧 Observation。这个函数适合教学内存副作用去重，但调用者仍必须在成功后尽快持久化 Checkpoint。

失败是否缓存？本课只在 operation 正常返回后记录。对于确定性失败可以保存完整 error Result，避免无意义重试；对于暂时性失败可能允许再次执行。状态策略必须显式，不能只存 output 字符串后猜测。

## 6. 原子持久化

```python
temporary.write_text(json.dumps(asdict(checkpoint)), encoding="utf-8")
temporary.replace(path)
```

与 Session 相同，临时文件降低半写 JSON。读取时必须验证 run_id、next_step 和数据类型；教学版保持最小，正式系统还需版本、校验和、锁或数据库事务。

Checkpoint 文件本身可能包含 Tool 参数和输出，应位于受控目录，不提交 Git，也不能在日志中无限复制敏感内容。

## 7. 两个错误直觉与纠正

### 误区一：恢复就是重新调用 `Runner.run(user_input)`

这会创建新 run_id、丢失事件顺序并重复 Tool。恢复必须加载原 Checkpoint，以原 run_id 和 next_step 继续。

### 误区二：所有 Tool 都天然幂等

read_file 重复通常无副作用，但 apply_patch、发送请求和发布命令可能不幂等。即使精确补丁第二次因 old_text 不存在而失败，也会让恢复路径出现误导 error，而不是原成功结果。

另一个误区是 call_id 可跨 Run 全局复用。去重键至少应包含 run_id + call_id，避免不同运行碰撞。

## 8. 完整中断与恢复轨迹

```text
run-1 step=1 ToolCall patch-1
execute_once: not found → apply patch → output="patched"
checkpoint.completed_calls[patch-1]="patched"
save checkpoint next_step=2
process stops

load run-1 checkpoint
execute_once(patch-1): found → return "patched"
actual write count remains 1
continue from step=2
```

恢复 Event 应追加 `run_resumed`，而不是再生成 `run_started`。序号接着旧事件增长，这是正式 Runtime 的进一步实现。

## 9. 幂等与 exactly-once 的边界

“最多一次”可能漏执行，“至少一次”可能重复，“恰好一次”需要执行与记录在同一事务边界。文件 Tool 可通过内容哈希和唯一 old_text 接近幂等；外部 API 应接受 idempotency key；命令 Tool 很难通用判断。

```text
Runtime key: run_id/call_id
Tool precondition: expected file hash or old_text
External service: idempotency key
```

三层结合比单纯在内存 set 中记 call_id 更可靠。本课先建立正确问题，不宣称 JSON Checkpoint 已实现分布式 exactly-once。

## 10. 运行、预期输出与故障实验

```powershell
python agent-from-scratch/course-checkpoints/06-session-reliability/steps/l23_checkpoint_resume.py
```

```text
first=patched resumed=patched side_effects=1 next_step=2
```

故障实验：恢复时换一个 call_id，观察副作用再次执行；删除 save 后模拟重启；让 operation 抛异常，确认未写 completed；把 Tool 名作为键，连续执行两次不同 Patch，观察错误去重。

## 11. 基础练习与进阶挑战

基础练习：记录两个不同 call_id，保存加载后分别复用。进阶挑战：把 completed_calls 值改成完整 ToolResult，并设计 `pending / completed / failed` 状态，分析每种崩溃窗口如何恢复。

答案见 [模块练习参考答案](模块练习参考答案.md)。

## 12. 自测、总结与下一课

1. Session 与 Checkpoint 分别解决什么问题？
2. 为什么去重键必须包含 call_id？
3. 先执行后记录与先记录后执行分别有什么窗口？
4. 为什么 JSON Checkpoint 不等于 exactly-once？
5. 哪些 Tool 需要额外幂等设计？

下一课 [L24 Config、错误、Retry 与 Timeout](L24-Config、错误、Retry与Timeout.md) 把恢复之外的暂时性失败纳入明确策略。

## 最终实现校准

正式 Checkpoint 保存 `completed_calls: call_id -> ToolResult`。恢复时相同 call_id 与相同工具名会复用已持久化结果并发出 `tool_reused` Event，不再次调用 Handler；相同 call_id 若对应不同工具则立即报错。但这仍不是事务型 exactly-once：进程可能在外部副作用已发生、Checkpoint 原子替换尚未完成之间崩溃。数据库写入、远程 API 和发布动作仍需幂等键、事务或人工确认。
