# L21 Session、Turn 与 Run：先分清三种“连续”，再谈记忆

> 建议学习时间：60–90 分钟。本课只建立会话身份和持久化，不进行上下文裁剪。

## 1. 本节要解决的真实问题

当前 Agent 每次 `Runner.run()` 都从空白开始。用户第二次说“继续修刚才的问题”，Runtime 不知道“刚才”是什么。最直接的做法是把所有 messages 存到一个全局列表，但它马上带来串话：两个用户是否共享历史？一次用户输入触发三步 Tool Loop，这算一个 Turn 还是三个？程序崩溃后重启，内存列表还在吗？

本课先定义三种身份：Session 是跨多次对话的会话容器；Turn 是一轮用户意图及其回答；Run 是 Runtime 为完成一个 Turn 发起的一次执行过程。只有分清它们，后续 Context、Checkpoint 和 Trace 才知道关联到哪里。

## 2. 问题链与生命周期

```text
Session session-1
  ├─ Turn turn-A: user asks to inspect
  │    └─ Run run-X: two model steps and one tool
  └─ Turn turn-B: user says continue
       ├─ Run run-Y: interrupted
       └─ Run run-Y resumed from checkpoint
```

Session 生命周期最长；Turn 表达产品层一次问答；Run 表达执行层一次状态机。一次 Turn 通常对应一个 Run，但恢复不应制造新的用户意图。把三者都叫 conversation id，会让日志和持久化无法解释。

## 3. 类比与两个 Coding Agent 案例

Session 像一个长期工单，Turn 像工单中的一条客户回复，Run 像工程师处理这条回复时启动的一次作业。作业可失败和恢复，但客户没有因此又发一条消息。

案例一：用户在同一 Session 先让 Agent 解释架构，再说“给刚才的 Runner 写测试”。第二个 Turn 需要第一轮结论。案例二：两个仓库各有独立 Session，即使用户输入都叫“继续”，也不能混用历史。第三个案例：同一 Turn 的 Run 在 Tool 执行后断电，恢复时 run_id 保持，便于事件继续排序。

## 4. Message 为什么携带 turn_id

```python
@dataclass(frozen=True)
class Message:
    role: str
    content: str
    turn_id: str
```

只存 role/content 可以喂给模型，却不能回答“这条 assistant 回复属于哪个用户请求”。turn_id 让持久化、裁剪和 UI 分组有稳定依据。Run 中的 Tool Event 不直接混进 Session messages；它们属于运行轨迹，最终摘要或回答才进入会话。

`Message` 是教学数据结构，不等于供应商 SDK 的 input item。内部会话模型与外部协议可以在边界转换。

## 5. 本课唯一代码增量：Session 与 Turn

```python
@dataclass
class Session:
    id: str
    messages: list[Message] = field(default_factory=list)

    def start_turn(self, user_input: str) -> Turn:
        turn = Turn(str(uuid4()), user_input)
        self.messages.append(Message("user", user_input, turn.id))
        return turn
```

Assistant 追加时必须给出已存在 turn_id，避免悬空回复。Session 不包含 current_step、Tool Results 或 Retry 次数，这些属于 Run。

## 6. 持久化边界与原子写入

```python
temporary.write_text(
    json.dumps(asdict(session), ensure_ascii=False, indent=2),
    encoding="utf-8", newline="\n",
)
temporary.replace(path)
```

严格 UTF-8 保留中文；先写临时文件再 replace，降低进程中断留下半份 JSON 的概率。原子替换不是完整数据库事务，但比直接覆盖更适合最小离线课程。

读取时重新构造 `Message`，而不是让 dict 混进类型列表。持久化格式是协议，一旦发布就需要考虑版本迁移；本课暂不增加 schema_version，但会把它留作挑战。

## 7. 两个错误直觉与纠正

### 误区一：Session 就是把完整 Event 全存进去

Event 数量远大于对话消息，包含工具参数和日志。把它们全部注入下一轮既浪费上下文，也可能重复旧 Tool Call。Session 保存产品层历史，Trace/Checkpoint 保存执行层事实。

### 误区二：每次调用 Runner 都创建新 Session

这样 run_id 和 session_id 只是两个随机数，没有跨 Turn 价值。Session 应由调用者选择和复用，Runner 只消费显式传入的历史。

另一个误区是全局单例 Session。并发任务会互相追加，测试顺序也影响结果。Session 必须显式创建或从 Store 加载。

## 8. 完整运行轨迹

```text
create Session("learning")
start_turn("inspect repository")
  → turn_id=t1
  → Message(user, inspect repository, t1)
Runner executes run_id=r1
append_assistant(t1, "ready")
  → Message(assistant, ready, t1)
save learning.json as UTF-8
load → same Session and two typed Messages
```

下一次 start_turn 会生成 t2，但仍保留 session id。Run id 则由 Runner 每次执行管理。

## 9. 关键边界与测试方法

源码见 [session.py](../../../agent-from-scratch/course-checkpoints/06-session-reliability/src/course_reliability/session.py)。测试不只断言文件存在，而要 round trip：构造中文消息、保存、加载、比较对象完全相等。

```python
store.save(session)
restored = store.load("session-1")
assert restored == session
```

还应测试未知 turn_id 被拒绝，两个 Session 文件互不覆盖，临时文件不会被当作正式会话读取。

## 10. 运行、预期输出与故障实验

```powershell
python agent-from-scratch/course-checkpoints/06-session-reliability/steps/l21_session_turn_run.py
```

```text
session=learning turns=1 messages=2
```

故障实验：用不存在 turn_id 追加回复；把 ensure_ascii 改为默认值比较可读性；直接覆盖文件并模拟只写一半；创建两个 Session 检查隔离；误把 Run Event 追加为 assistant message，观察下一轮上下文为何混乱。

## 11. 基础练习与进阶挑战

基础练习：在同一 Session 创建两个 Turn，并按 turn_id 分组打印。进阶挑战：为 JSON 增加 `schema_version=1`，设计读取未来版本时的明确错误，而不是默默忽略未知字段。

答案见 [模块练习参考答案](模块练习参考答案.md)。

## 12. 自测、总结与下一课

1. Session、Turn、Run 的生命周期分别是什么？
2. 一个 Turn 为什么可能包含恢复后的同一 Run？
3. Message 为什么携带 turn_id？
4. 为什么不把全部 Event 存进 Session messages？
5. 原子替换解决了什么、没解决什么？

下一课 [L22 上下文预算与压缩](L22-上下文预算与压缩.md) 讨论 Session 可以长期增长，但每次模型调用不能无限携带全部历史。

## 最终实现校准

正式包使用 `Message(role, content, turn_id)` 与 `Turn(id, user_input)`，新用户输入通过 `start_turn` 建立稳定归属，assistant 回复必须引用已存在的 turn_id。Session/Checkpoint ID 仅允许 1–64 位 ASCII 字母、数字、下划线与连字符，并在拼接后再次做目录包含校验；旧版仅含 role/content 的消息会在加载时迁移到生成的 turn_id。
