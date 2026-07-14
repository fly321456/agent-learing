# A04 最小 Reviewer 实验

> 选修课｜建议时长：60–90 分钟｜前置课程：A01–A03

## 1. 本节要解决的真实问题

“再加一个 Reviewer，质量肯定更高”听起来合理，却不是工程结论。Reviewer 会新增一次或多次模型调用、更多上下文传递、更长延迟，也可能只是重复 Executor 的判断。若没有单 Agent 基线和同一组测试任务，我们只能展示一个更复杂的 Demo，无法证明复杂度值得保留。

本课要回答一个可证伪的问题：**在候选结果和验收标准不变时，独立 Reviewer 是否减少了错误接受（false acceptance），收益是否大于新增通信成本？**

错误接受指结果缺少必要内容，却仍被系统标记为通过。Coding Agent 中常见例子是“代码已修改但没有测试”，Executor 因为完成了主要实现而自我认可，最终答案却给出“已全部验证”。Reviewer 的价值不是写一遍同样的答案，而是依据独立标准发现这种遗漏。

## 2. 先固定单 Agent 基线

比较实验必须只改变一个变量。这里固定候选结果、必需片段和任务顺序，只在第二组增加 Reviewer：

~~~text
单 Agent 基线：Executor 产生候选结果 -> Executor 自己批准
Reviewer 方案：Executor 产生同一候选 -> Reviewer 按同一标准检查

保持不变：任务集、候选文本、验收标准、统计方法
唯一变量：是否经过独立 Reviewer
~~~

为什么基线故意采用“总是自我批准”的确定性脚本？因为本实验要隔离审查边界，而不是比较两个随机模型。真实模型每次输出可能变化，会掩盖 Reviewer 的实际贡献。先用离线确定性案例验证指标和决策逻辑，再考虑在线实验。

## 3. 两个具体案例

案例一是合格候选：`"code plus tests"`，验收标准要求同时出现 `code` 与 `tests`。单 Agent 和 Reviewer 都应接受它。若 Reviewer 拒绝，产生的是误拒绝；本实验虽未统计误拒绝，但正式评测不能忽略。

案例二是不合格候选：`"code only"`，仍要求 `code` 与 `tests`。单 Agent 自审会接受，形成一次错误接受；Reviewer 检查到缺少 `tests`，应返回拒绝及明确问题。

~~~python
cases = [
    ReviewCase("good", "code plus tests", ("code", "tests")),
    ReviewCase("bad", "code only", ("code", "tests")),
]
~~~

这两个案例很小，却具备完整实验结构：有正例、有反例、有机器可判定的标准。若案例只有失败样本，Reviewer 只要全部拒绝就能获得虚假的“完美成绩”。

## 4. 核心概念：先定义指标，再选择架构

本课使用三个指标：

| 指标 | 含义 | 越小越好吗 |
| --- | --- | --- |
| `single_false_accepts` | 单 Agent 接受了多少不合格结果 | 是 |
| `reviewer_false_accepts` | Reviewer 方案接受了多少不合格结果 | 是 |
| `communication_chars` | Executor 与 Reviewer 往返文本字符数 | 是，但不能脱离质量看 |

质量增益定义为：

~~~text
gain = single_false_accepts - reviewer_false_accepts
~~~

当 `gain <= 0` 时，Reviewer 没有减少错误接受，应默认保留单 Agent。只有 `gain > 0`，本实验才推荐 Reviewer，同时报告通信字符数，而不是隐藏成本。这个规则很保守，因为它还没有统计延迟、Token、误拒绝和维护成本；真实项目的保留门槛应该更高。

## 5. Reviewer 协议如何保持最小

`ReviewCase` 同时保存候选内容和可验证标准，`Review` 只返回批准状态与问题列表：

~~~python
@dataclass(frozen=True)
class ReviewCase:
    id: str
    candidate: str
    required_fragments: tuple[str, ...]

@dataclass(frozen=True)
class Review:
    approved: bool
    issues: tuple[str, ...]
~~~

Reviewer 不修改候选结果，也不替 Executor 重做任务。这个边界非常重要：审查与修复是两个动作。若 Reviewer 一边改代码一边批准，评测就无法区分“审查发现问题”还是“第二个 Agent 重新完成了任务”。

最小审查函数是确定性的：

~~~python
def review_candidate(case: ReviewCase) -> Review:
    issues = tuple(
        f"Missing required fragment: {fragment}"
        for fragment in case.required_fragments
        if fragment not in case.candidate
    )
    return Review(not issues, issues)
~~~

这不是通用代码质量审查器，而是教学用的可判定代理。它让我们专注于协议、指标和架构决策，而不是把模型随机性误当成系统能力。

## 6. 比较函数逐段推导

比较函数对每个案例运行相同标准。单 Agent 基线自我批准所有候选，因此每个实际不合格案例都会形成错误接受。Reviewer 方案则记录两次消息：候选从 Executor 发给 Reviewer，结论再返回 Executor。

~~~python
def compare_single_and_reviewer(cases: list[ReviewCase]) -> Comparison:
    single_false_accepts = sum(
        not review_candidate(case).approved for case in cases
    )
    shared = SharedState()
    reviewer_false_accepts = 0
    for case in cases:
        shared.record("executor", "reviewer", case.candidate)
        review = review_candidate(case)
        response = "approved" if review.approved else "; ".join(review.issues)
        shared.record("reviewer", "executor", response)
    return Comparison(
        single_false_accepts,
        reviewer_false_accepts,
        shared.communication_chars,
    )
~~~

实验实现还保留了 Reviewer 错误接受的显式判断。当前确定性 Reviewer 不会漏掉必需片段，所以值为零；字段仍然存在，是为了让接口表达真实评测目标，而不是把“Reviewer 永远正确”写死在结果模型中。

## 7. 完整运行轨迹

对两个案例逐项手工追踪：

~~~text
case=good
  actual_valid=true
  single_agent=approved
  reviewer=approved
  false_accept_delta=0

case=bad
  actual_valid=false
  single_agent=approved       -> single_false_accepts += 1
  reviewer=rejected
  issue="Missing required fragment: tests"

summary
  single_false_accepts=1
  reviewer_false_accepts=0
  gain=1
  communication_chars=83
  recommended=true
~~~

`communication_chars=83` 来自四条实际消息内容，而不是静态常量。只要改变案例文本或审查结论，成本就会改变，这使测试能防止“指标只是写死打印”的假评测。

## 8. 运行命令与预期输出

运行本课步骤：

~~~powershell
cd agent-from-scratch
python course-labs/multi-agent/steps/a04_reviewer_comparison.py
~~~

预期输出：

~~~text
single_false_accepts=1 reviewer_false_accepts=0 recommended=true
~~~

运行完整选修 Demo 可以同时看到可拆分性审计、局部失败和 Reviewer 比较：

~~~powershell
python course-labs/multi-agent/demo.py
python -m pytest -q tests/test_course_multi_agent.py
~~~

测试还构造 `Comparison(0, 0, 100)`，验证没有质量增益时必须推荐单 Agent，即使 Reviewer 流程本身运行正常。

## 9. 两个错误直觉与反例纠错

**错误直觉一：独立 Reviewer 一定比自审可靠。** 如果 Reviewer 与 Executor 使用相同上下文、相同盲点和模糊标准，它可能只是重复同一个错误。反例：所有候选本来都合格，单 Agent 与 Reviewer 错误接受都为零，Reviewer 只增加 100 个通信字符。此时 `gain=0`，应回退单 Agent。

**错误直觉二：错误接受下降就足以证明方案更好。** 若 Reviewer 把所有结果都拒绝，错误接受会降到零，但误拒绝和人工返工会暴涨。正式评测还应记录误拒绝率、任务完成率、调用次数、Token、延迟和失败类型。本实验只证明最小质量增益，不宣称完成了全部商业决策。

另一个常见错误是同时更换模型、重写 Prompt、增加 Reviewer 和扩大任务集。结果改善后无法知道是哪项变化带来收益。实验必须一次只改变一个变量。

## 10. 基础练习与最终挑战

基础练习：增加第三个案例，候选含 `tests` 却缺少 `code`，手工预测两个错误接受指标与通信字符数，再运行验证。解释为什么字符数变化但架构决策仍可能不变。

进阶练习：为 `Comparison` 增加 `reviewer_false_rejects`，同时加入一个会被过严 Reviewer 拒绝的有效案例。设计决策函数时，不要简单相减；先说明错误接受和误拒绝在你的项目中各自成本是多少。

最终挑战：从主线 20 个 Coding Agent 评测任务中选 5 个适合审查的任务，冻结单 Agent 输出，再让 Reviewer 只读这些输出。记录质量增益、额外调用、延迟和通信量。若没有稳定增益，写出“拒绝引入多 Agent”的结论，这同样是合格实验结果。

## 11. 自测问题

1. 为什么比较 Reviewer 前必须冻结任务集、候选结果和验收标准？
2. 错误接受与普通执行失败有什么区别？
3. Reviewer 为什么只审查而不直接修改候选结果？
4. 当 `single_false_accepts` 和 `reviewer_false_accepts` 都为零时，为什么默认选单 Agent？
5. 除通信字符数外，真实项目还必须记录哪些收益与成本？

## 12. 课程总结与模块结论

本课没有把多 Agent 当作终点，而是把它当作一项需要证据的架构假设。最小 Reviewer 只有在同一任务集上减少错误接受时才获得保留资格；即使有收益，也必须同时报告通信成本。没有增益时回退单 Agent，不是实验失败，而是避免了无价值复杂度。

至此，多 Agent 选修形成完整闭环：A01 判断任务是否值得拆分，A02 定义角色协议，A03 明确状态所有权与局部失败，A04 用基线和指标决定是否保留 Reviewer。你应当带走的不是一种固定架构，而是一套“先审计、再隔离、后评测、可回退”的工程方法。

[上一课：A03 共享状态、成本与局部失败](A03-共享状态、成本与局部失败.md)｜[模块练习参考答案](模块练习参考答案.md)｜[模块验收与面试](模块验收与面试.md)｜[返回选修导学](模块导学.md)
