# A02 Planner–Executor–Reviewer 协议：角色靠数据契约协作，不靠猜

> 建议学习时间：60–90 分钟。本课实现确定性 Planner/Executor 数据流，Reviewer 只定义输入输出边界。

## 1. 本节要解决的真实问题

多 Agent 常用三段 Prompt：“你是 Planner”“你是 Executor”“你是 Reviewer”，然后把自然语言整段互相转发。Executor 不知道计划项是否唯一，Reviewer 不知道审查哪个产物，失败后 Planner 也不知道重试哪一项。角色存在了，协议却不存在。

本课定义最小契约：Planner 产生带稳定 id 的 PlanItem；Executor 对每项返回 WorkResult；Reviewer 读取候选与验收条件，返回 approved 和 issues。每层输出可测试、可序列化、可追踪。

问题链是：计划项需要哪些字段？为什么 objective 与实现指令要分开？Executor 异常如何局部化？Reviewer 能否直接修改产物？角色是否共享完整消息历史？

## 2. 三个角色的职责

```text
Planner：把目标拆成有边界的 PlanItem，不执行 Tool
Executor：执行一项，返回结果或错误，不改计划
Reviewer：按显式验收条件审查，不偷偷重做任务
```

职责分离的价值是失败可定位。Planner 质量差看计划；Executor 失败看 WorkResult；Reviewer 漏缺陷看 Review。若每个角色都能改计划、执行和批准，系统仍是三个大而全 Agent。

## 3. 类比与两个计划案例

协议像工单系统：产品经理创建工单号和目标，开发者提交结果，审查者给通过或问题列表。口头说“你看着办”无法追踪。

案例一：`inspect`、`test`、`document` 三项互相独立，各有 task-01/02/03。案例二：“修改代码并确保没问题”只有一个模糊项，Executor 不知道测试标准，Reviewer 也无法判断完成。

PlanItem 应描述可验收 outcome，例如“运行单元测试并保存退出码”，而非规定内部每一行操作。

## 4. PlanItem 数据模型

```python
@dataclass(frozen=True)
class PlanItem:
    id: str
    objective: str

def create_plan(objectives):
    return [
        PlanItem(f"task-{index:02d}", objective)
        for index, objective in enumerate(objectives, 1)
    ]
```

稳定 id 贯穿 Event、Result 和 Review。教学版字段最少；真实项目可增加 dependencies、acceptance、risk 和 assigned_role，但只有实际需要时再加。

计划顺序不自动表示依赖。若 task-02 依赖 task-01，应显式声明，而不是让 Executor 猜。

## 5. 本课唯一代码增量：WorkResult

```python
@dataclass(frozen=True)
class WorkResult:
    item_id: str
    status: str
    output: str = ""
    error: str | None = None
```

WorkResult 与主线 ToolResult 思路一致：成功和失败使用同一类型，item_id 关联计划。Executor 抛异常时，协调器转换为 status=error，而不是让整个计划状态消失。

output 应是精简产物或引用，不应无上限复制全部 Trace。

## 6. 执行协议

```python
def execute_plan(plan, executor):
    state = ExecutionState(plan)
    for item in plan:
        try:
            state.results.append(WorkResult(item.id, "success", executor(item)))
        except Exception as exc:
            state.results.append(WorkResult(item.id, "error", error=str(exc)))
    return state
```

教学版顺序执行，便于观察。可并行不等于必须并行；只有独立 PlanItem 才能并发，并且结果仍按 item_id 关联。

协调器记录状态，不替 Executor 修复输出。

## 7. Reviewer 协议

```python
@dataclass(frozen=True)
class Review:
    approved: bool
    issues: tuple[str, ...]
```

Reviewer 必须依据 acceptance 条件，issues 应具体可行动，例如“缺少测试”，而不是“可以更好”。Reviewer 默认不修改候选，避免审查与执行混在一起；需要修复时生成新的 Executor 任务。

Reviewer 自身也可能错，A04 会与真实 acceptance 比较 false acceptance。

## 8. 两个错误直觉与纠正

### 误区一：Planner 输出越详细越好

过度规定实现会限制 Executor，也增加 token。计划应明确目标、依赖和验收，不复制全部代码 Context。

### 误区二：Reviewer 发现问题后直接修最快

这样无法区分谁产生修改，也绕过 Executor 权限和测试协议。小系统可合并角色，但既然选择多 Agent，就应保持审查结果可追踪。

另一个误区是所有角色共享完整 Session。每个角色只应得到完成职责所需 Context，降低成本和提示注入传播。

## 9. 完整协议轨迹

```text
Planner → [task-01 inspect, task-02 test, task-03 document]
Executor(task-01) → success done:inspect
Executor(task-02) → error tests unavailable
Executor(task-03) → success done:document
Coordinator → ExecutionState preserves all three Results
Reviewer → review successful artifacts against acceptance
```

task-02 失败不会把 task-01/03 清空。是否重试由错误类型和依赖决定。

## 10. 运行、预期输出与故障实验

```powershell
python agent-from-scratch/course-labs/multi-agent/steps/a02_protocols.py
```

```text
planned=3 completed=3
```

故障实验：制造重复 PlanItem id；让第二项抛异常；交换执行顺序；给 Reviewer 一个没有 acceptance 的候选；让 Reviewer 直接覆盖 Executor output，分析审计问题。

## 11. 基础练习与进阶挑战

基础练习：为 PlanItem 增加 acceptance，并让 Reviewer逐项检查。进阶挑战：加入 dependencies，做拓扑顺序验证；检测循环依赖并返回结构化计划错误。

答案见 [模块练习参考答案](模块练习参考答案.md)。

## 12. 自测、总结与下一课

1. 角色 Prompt 为什么不能代替数据协议？
2. PlanItem id 解决什么关联问题？
3. WorkResult 为什么要统一成功与失败？
4. Reviewer 为什么默认不直接修改候选？
5. 哪些 PlanItem 才适合并行执行？

下一课 [A03 共享状态、成本与局部失败](A03-共享状态、成本与局部失败.md) 将计算角色通信成本，并设计失败隔离与恢复策略。
