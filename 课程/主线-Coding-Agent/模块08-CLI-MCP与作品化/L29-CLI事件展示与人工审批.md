# L29 CLI 事件展示与人工审批：产品界面不应侵入 Runtime

> 建议学习时间：60–90 分钟。本课把前七个模块的协议交付为可使用 CLI，但仍使用离线 Event 和可注入输入完成核心实验。

## 1. 本节要解决的真实问题

Runner 已能返回 RunResult，Trace 也能记录 Event，但普通用户不应该等任务结束后再打开 JSONL 才知道 Agent 正在做什么。Coding Agent 可能读取文件、请求补丁、等待审批、运行测试或重试模型；CLI 需要即时展示这些状态，并在高风险 Tool 前询问用户。

最直接的实现是在 Runner 内到处 `print()` 和 `input()`。这样 Runtime 无法在测试、Web、服务端或无交互环境复用，审批也难以注入自动策略。本课建立两条边界：Runner 只产生结构化 Event 和调用 approval callback；CLI 负责把 Event 渲染成人类文本，并把用户输入转换为布尔决定。

问题链是：哪些 Event 值得展示？最终答案写 stdout 还是 stderr？审批无输入时为什么默认拒绝？是否显示完整 Tool 参数？Session、Resume、Trace 参数由谁解析？

## 2. CLI 在架构中的位置

```text
User terminal
  → argparse / command options
  → Agent + Runner + ToolContext
  ← Event Sink: progress to stderr
  ← RunResult.content: final answer to stdout
```

CLI 是 Adapter（适配器），不是 Runtime 核心。它把命令行参数转换为配置，把 Event 转换为文本，把键盘输入转换为审批结果。Runner 不知道终端颜色、提示语或 `argparse`。

这种边界让同一 Runtime 后续可接 Web、IDE 或测试 Sink，而不改 Agent Loop。

## 3. 两个实际使用案例

案例一：Agent 读取文件并完成。stderr 显示 `[1] tool -> read_file` 和 `[1] tool <- read_file (success)`，stdout 最后只输出答案。用户可以把最终答案通过管道写文件，同时仍在终端看到进度。

案例二：Agent 请求 `run_command(["pytest"])`。CLI 先展示 Tool 名和参数，再提示 `[y/N]`。用户直接按 Enter，审批结果是 False，Tool handler 不执行。默认值必须安全，因为非交互管道、误触回车和输入中断都不应自动放行副作用。

第三个案例是 `--trace trace.jsonl`：同一个 Event 先由 CLI 展示，再由 JsonlTraceWriter 持久化，二者不重新发明事件格式。

## 4. Event 渲染不是业务控制

```python
def format_event(event):
    if event.type == "tool_called":
        return f"[{event.step}] tool -> {event.data['name']}"
    if event.type == "tool_completed":
        return f"[{event.step}] tool <- {event.data['name']} ({event.data['status']})"
```

format_event 是纯函数：输入 Event，输出字符串或 None。它不能决定 Tool 是否执行，也不能修改 Event。未知类型返回 None，让 CLI 逐步增加展示而不破坏 Runtime 新事件。

正式 CLI 可展示 `llm_retry`、`run_resumed` 和 `max_steps`，但不要把每个底层调试 Event 都倾倒给普通用户。

## 5. 本课唯一代码增量：可注入审批

```python
def request_approval(tool_name, arguments, input_fn=input):
    prompt = f"Allow {tool_name} with {arguments}? [y/N] "
    return input_fn(prompt).strip().lower() in {"y", "yes"}
```

输入函数可注入，测试可以传 `lambda _: "yes"` 或空字符串，不需要真的阻塞终端。只有明确 y/yes 放行，其他输入一律拒绝。

模块 5 的 ToolManager 仍是最终执行闸门。CLI 只提供 callback，不能因为界面显示过“Approval required”就绕过 Manager 检查。

## 6. stdout 与 stderr 的契约

```text
stdout: 最终内容，便于管道和脚本消费
stderr: 进度、审批提示、警告、非完成原因
exit code 0: completed
exit code non-zero: denied / error / max_steps
```

若 Event 与答案都写 stdout，`coding-agent task > answer.txt` 会混入工具日志。退出码比搜索输出中的“success”更稳定，自动化调用者应同时读取 RunResult reason 和进程 code。

CLI 的人类可读文本不是新的 Runtime 协议；机器集成优先使用结构化 API 或 JSON 模式。

## 7. 两个错误直觉与纠正

### 误区一：CLI 只需最后打印答案

长任务没有过程反馈会让用户误以为卡死，也无法在危险操作前参与。关键 Event 和审批是 Coding Agent 产品体验的一部分。

### 误区二：为了方便演示，审批默认 yes

演示环境最容易被复制到真实项目。安全默认必须从第一版保持；自动批准应是显式策略，并受工作区、Tool 风险和参数限制。

另一个误区是把完整源码和环境变量都打印在审批提示中。用户需要足够决策的信息，但敏感值应脱敏，长参数应截断并允许查看详情。

## 8. 完整 CLI 轨迹

```text
$ coding-agent "run tests" --workspace repo --trace run.jsonl
[1] tool -> run_command                         # stderr
Approval required: run_command {command:[...]}  # stderr
Allow this operation? [y/N] y
[1] tool <- run_command (success)               # stderr
All tests passed.                               # stdout
process exit code=0
```

拒绝轨迹则产生 ToolResult denied、Run finish_reason=denied、stderr 显示结束原因，退出码非零。CLI 不应偷偷再次询问或换另一个 Tool 名绕过拒绝。

## 9. Session、Resume 与 Trace 参数

正式项目的 CLI 还提供 `--session`、`--resume RUN_ID`、`--workspace`、`--max-steps` 和 `--trace`。参数解析只负责建立对象：SessionStore、CheckpointStore、ToolContext 和 Event Sink；真正的恢复与裁剪仍由对应模块执行。

```python
if bool(args.prompt) == bool(args.resume):
    parser.error("provide either a prompt or --resume")
```

Prompt 与 Resume 互斥，避免调用者既创建新 Run 又要求恢复旧 Run。模型必须由参数或环境变量显式指定，不写永久默认模型名。

## 10. 运行、预期输出与故障实验

```powershell
python agent-from-scratch/course-checkpoints/08-cli-mcp-final/steps/l29_cli_events_approval.py
```

```text
event=[2] tool <- apply_patch (success) approval=false
```

故障实验：输入空字符串、no、YES 和任意文字；让未知 Event 进入 formatter；把进度错误写入 stdout，观察管道污染；在审批前隐藏 arguments，判断用户是否有足够信息；让 input_fn 抛 EOFError，设计 fail closed 处理。

## 11. 基础练习与进阶挑战

基础练习：增加 denied、timeout 和 llm_retry 的展示，并保持纯函数。进阶挑战：实现 `--json` 输出，每行输出 Event JSON，最终输出 RunResult JSON；说明如何避免与人类文本混用。

答案见 [模块练习参考答案](模块练习参考答案.md)。

## 12. 自测、总结与下一课

1. 为什么 CLI 应是 Runtime 的 Adapter？
2. Event 展示和审批控制分别属于哪一层？
3. 为什么最终答案与进度应分 stdout/stderr？
4. 空输入为什么必须默认拒绝？
5. `--resume` 与新 prompt 为什么互斥？

下一课 [L30 MCP 到底标准化什么](L30-MCP到底标准化什么.md) 将把 Tool 从单个 CLI 进程扩展为可被标准客户端发现和调用的协议服务。
