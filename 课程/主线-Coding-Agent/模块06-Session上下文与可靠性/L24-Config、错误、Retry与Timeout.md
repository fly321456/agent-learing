# L24 Config、错误、Retry 与 Timeout：不是所有失败都值得再试一次

> 建议学习时间：60–90 分钟。本课完成模块 6，建立配置校验和分类重试。

## 1. 本节要解决的真实问题

真实模型调用会遇到网络中断、限流、服务端错误，也会遇到非法参数、认证失败和无法解析的响应。若 Runner 对所有 Exception 都重试三次，确定性错误只会重复费用和延迟；若完全不重试，短暂网络抖动又让长任务轻易失败。

本课建立 Error Taxonomy（错误分类）与 Retry Policy：只有明确标记为 Retryable 的暂时性错误进入有限指数退避；Deterministic 错误立即上抛或结束 Run。Attempts、Context 预算和 max_steps 由经过校验的 Config 提供，不在代码各处读取环境变量。

## 2. 配置为什么也是可靠性边界

```text
Environment strings
  → parse once
  → RuntimeConfig validation
  → explicit objects passed to Runner/Context
```

`AGENT_MAX_STEPS=0`、负 Timeout、非整数 Retry 次数都应在启动时失败，而不是运行到关键步骤才表现异常。配置与运行状态分开：retry_attempts 是策略，当前 attempt 是一次调用状态。

教学版从 Mapping 读取，测试无需污染真实环境；应用入口可以传 `os.environ`。

## 3. 两类错误与具体案例

Retryable：临时连接失败、429 限流、部分 5xx、短暂超时。重试可能在不修改请求的情况下成功。

Deterministic：API Key 无效、模型名不存在、Tool 参数 JSON 非法、响应协议缺字段。相同输入原样重试大概率仍失败，需要改配置、代码或上下文。

案例一：第一次模型调用抛 `RetryableError("temporary")`，第二次返回 recovered，记录一次 retry Event。案例二：抛 `DeterministicError("invalid response")`，即使策略 attempts=3，也只调用一次。

## 4. RuntimeConfig 的最小实现

```python
@dataclass(frozen=True)
class RuntimeConfig:
    max_steps: int = 8
    context_chars: int = 40_000
    retry_attempts: int = 2
```

`from_mapping()` 负责字符串到整数转换，`__post_init__()` 负责正数约束。模型名不在教学 Config 中，因为本模块完全离线；正式应用还应显式要求 `OPENAI_MODEL`，不把某个模型名写成永久默认。

Config 不应成为全局 mutable 字典。显式 dataclass 让类型、默认值和校验集中，并可直接注入测试。

## 5. 本课唯一代码增量：RetryPolicy

```python
for attempt in range(1, attempts + 1):
    try:
        return operation()
    except RetryableError as exc:
        if attempt >= attempts:
            raise
        emit_retry(attempt, exc)
        sleep(base_delay * 2 ** (attempt - 1))
```

except 只捕获 RetryableError，因此 DeterministicError 和编程错误自然退出。最后一次失败必须重新 raise，不能跌出循环返回 None。`attempts` 表示总尝试次数，不是“额外重试次数”，文档与配置必须一致。

## 6. Backoff、Timeout 与预算

指数退避让连续请求间隔增长，避免服务异常时同步轰炸。生产系统通常再加 jitter，减少多个客户端同一时刻重试。教学测试用 base_delay=0，保持快速确定。

Timeout 是每次 attempt 的时间边界，Retry 是跨 attempt 的策略，max_steps 是 Agent Loop 的决策预算，三者不能混用：

```text
request timeout → one model attempt stopped
retry attempts  → how many temporary attempts
max_steps       → how many model decisions in one Run
```

总时长还应有 Run deadline，否则每步多次 Retry 会放大整体延迟。

## 7. 两个错误直觉与纠正

### 误区一：捕获 Exception 最稳妥

它会吞掉代码 Bug、配置错误和确定性协议错误，使系统反复执行错误路径。只捕获你能采取明确恢复动作的异常。

### 误区二：Retry 能提高所有任务成功率

Retry 只对暂时性失败有效，还会增加延迟、费用和重复副作用风险。模型调用相对易重试；Tool 副作用必须先确认幂等。

另一个误区是 Retry 不需要 Event。没有 attempt、错误和延迟记录时，用户只看到“很慢”，工程师不知道请求重试了几次。

## 8. 完整成功与失败轨迹

```text
Policy attempts=2 base_delay=0
attempt 1 → RetryableError temporary
emit {type: retry, attempt: 1, error: temporary}
attempt 2 → "recovered"
return recovered

Policy attempts=3
attempt 1 → DeterministicError invalid response
not caught → stop immediately
actual calls=1
```

若两次都 Retryable，第二次异常原样抛出，由 Runner 记录 llm_failed 和 Run error。

## 9. 错误分类责任

Provider adapter 最了解 HTTP 状态和 SDK 异常，应把它们翻译为内部 Retryable 或 Deterministic LLM Error。Runner 不应通过错误消息字符串包含“429”来猜测。ToolManager 则负责 denied、timeout、error 等 Tool Result。

```python
if status == 429 or status >= 500:
    raise RetryableError(...)
raise DeterministicError(...)
```

分类可能不完美，因此模块 7 要统计重试后成功率和错误分布，用证据调整策略。

## 10. 运行、预期输出与故障实验

```powershell
python agent-from-scratch/course-checkpoints/06-session-reliability/steps/l24_retry_config.py
cd agent-from-scratch
python -m pytest -q tests/test_course_module6.py
```

```text
attempts=2 result=recovered max_steps=8
```

故障实验：把配置设为 0 或非整数；让两次都暂时失败；抛 DeterministicError 检查调用数；把 except 改成 Exception 观察错误重试；使用非零 base_delay 记录总耗时。

## 11. 基础练习与进阶挑战

基础练习：收集 retry Events，并断言 attempt 从 1 开始。进阶挑战：增加可注入 `sleep_fn` 与确定性 jitter，避免测试真实等待；再设计 Run deadline 如何与单次 Timeout 协作。

答案见 [模块练习参考答案](模块练习参考答案.md)。

## 12. 自测、总结与下一模块

1. Retryable 与 Deterministic 错误依据是什么？
2. 为什么 RetryPolicy 不捕获所有 Exception？
3. attempts=2 表示调用几次？
4. Timeout、Retry、max_steps 分别限制什么？
5. 为什么错误分类应主要发生在 Provider adapter？

模块 6 已形成可保存、可裁剪、可恢复、可分类失败的 Runtime 基础。下一模块从 [L25 FakeLLM 与单元测试](../模块07-测试评测与可观测性/L25-FakeLLM与单元测试.md) 开始，用系统测试和评测证明这些协议长期稳定。
