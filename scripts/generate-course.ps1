param([string]$RepositoryRoot = (Split-Path $PSScriptRoot -Parent))

$ErrorActionPreference = 'Stop'
$utf8 = New-Object System.Text.UTF8Encoding($false)
$courseRoot = Join-Path $RepositoryRoot '课程'
$mainRoot = Join-Path $courseRoot '主线-Coding-Agent'
$optionalRoot = Join-Path $courseRoot '选修模块'

function Write-Utf8([string]$Path, [string]$Content) {
    $directory = Split-Path $Path -Parent
    New-Item -ItemType Directory -Path $directory -Force | Out-Null
    [System.IO.File]::WriteAllText($Path, $Content.Trim() + "`n", $utf8)
}

$modules = @(
    @{ Id='01'; Name='Agent核心认知'; Outcome='能用自己的话解释 Agent，并用离线脚本演示 Think-Act-Observe。'; Checkpoint='01-agent-concepts'; Lessons=@(
        @('L01','什么是Agent','普通 LLM 为什么还不是 Agent？','Agent 是能在环境中持续观察并决定下一步的运行系统，而不是一次回答。','把一次性回答改成多步行动记录','python demo.py','THINK -> ACT -> OBSERVE -> FINISH'),
        @('L02','Agent四要素','一个 Agent 最少由哪些部分组成？','LLM 负责决策，Tool 负责执行，Loop 负责持续运行，Environment 提供可观察和可改变的外部世界。','为离线脚本标出 LLM、Tool、Loop、Environment','python demo.py','四个角色都能在输出中定位'),
        @('L03','Agent与Workflow','什么时候应该用 Agent，什么时候固定流程更好？','Workflow 的路径由人预先定义；Agent 的下一步由模型根据观察动态决定。稳定、可枚举的流程优先使用 Workflow。','比较固定分支与动态决策两条执行轨迹','python demo.py','同一目标出现两种不同执行路径'),
        @('L04','手工走一遍Think-Act-Observe','模型调用工具后为什么还必须继续思考？','Observe 是工具结果形成的新事实；只有把它送回决策者，系统才能根据结果调整下一步。','完成第一个 ScriptedLLM 离线循环','python demo.py','脚本经历至少一次观察后再结束')
    )},
    @{ Id='02'; Name='LLM与Tool Calling'; Outcome='理解真实 Responses API 的输入输出，并完成一次单 Tool 固定往返。'; Checkpoint='02-tool-calling'; Lessons=@(
        @('L05','Message、Instructions与Context','模型到底看到了哪些信息？','Instructions 定义长期行为边界，Message 表达当前对话，Context 是本次调用实际携带的全部信息。','打印并检查一次模型请求的输入列表','python demo.py','输出 system 与 user 两类输入'),
        @('L06','第一次Responses API文本调用','如何把一次普通文本调用接入项目？','Responses API 接收 input 并返回 output；在线实验是选做，离线 ScriptedClient 保证必修路径可重复。','增加离线客户端与可选 OpenAI 客户端','python demo.py','offline response: ready'),
        @('L07','Tool Schema与function_call','模型为什么知道工具名称和参数？','Tool Schema 是给模型阅读的结构化接口说明；function_call 是调用请求，不是函数执行结果。','定义 get_current_time 的 JSON Schema 并解析调用请求','python demo.py','function_call: get_current_time'),
        @('L08','执行Tool并回传结果','Python 执行结果怎样回到模型？','Runtime 用 call_id 关联 function_call 与 function_call_output，再发起下一次模型调用获得最终回答。','完成固定两次模型调用的单 Tool 往返','python demo.py','final: current time received')
    )},
    @{ Id='03'; Name='从零实现Agent Loop'; Outcome='得到约 150 行、支持多 Tool 和受控终止的单文件 Agent。'; Checkpoint='03-agent-loop'; Lessons=@(
        @('L09','从固定调用到while循环','任务需要几次工具调用无法预先确定怎么办？','Agent Loop 每轮检查模型是要调用工具还是完成回答，运行路径由观察结果决定。','把固定两次调用重构成 while 循环','python demo.py','loop completed'),
        @('L10','Tool Registry与通用路由','每增加一个 Tool 都写 if/elif 会发生什么？','Tool Registry 用名称映射 Schema 和 handler，让 Runner 不依赖具体业务工具。','用字典注册 calculator 与 current_time','python demo.py','calculator=42'),
        @('L11','多Tool与同轮多调用','一轮响应包含多个 ToolCall 时如何处理？','Runtime 必须按稳定顺序处理完整调用列表并逐个回传结果，不能只取第一个。','让一轮同时调用 calculator 和 current_time','python demo.py','tool_results=2'),
        @('L12','终止条件与错误','如何保证 Agent 不会无限运行或因未知工具崩溃？','completed、max_steps、unknown_tool 和 tool_error 必须成为明确且可测试的结束或恢复语义。','加入 max_steps、未知 Tool 和异常包装','python demo.py','finish_reason=completed')
    )},
    @{ Id='04'; Name='Runtime模块化重构'; Outcome='把单文件 Agent 重构成职责清晰、可安装和可测试的 Runtime 包。'; Checkpoint='04-runtime-refactor'; Lessons=@(
        @('L13','Agent配置边界','为什么能跑的单文件代码还需要拆分？','Agent 描述名称、指令、模型和工具；Runner 才拥有每次运行的临时状态和生命周期。','抽出 Agent 配置对象','python demo.py','agent=coding-agent'),
        @('L14','LLM接口与LLMResponse','Runner 为什么不能直接读取供应商对象？','BaseLLM 隔离供应商调用，LLMResponse 只表示一次模型调用的标准结果。','抽出 BaseLLM、FakeLLM 与 LLMResponse','python demo.py','llm_response=completed'),
        @('L15','ToolManager与ToolResult','工具成功、拒绝和失败如何统一表达？','ToolSpec 描述工具，ToolManager 路由执行，ToolResult 用稳定状态表达结果。','抽出 ToolSpec、ToolManager 与 ToolResult','python demo.py','tool_status=success'),
        @('L16','Runner、RunResult与Event','调用者怎样拿到完整运行过程？','RunResult 表示整次运行，Event 按 run_id、步骤和序号记录过程；它们不能与单轮 LLMResponse 混用。','让 Runner 返回 RunResult 并累计 Event','python demo.py','finish_reason=completed events>0')
    )},
    @{ Id='05'; Name='安全Coding Tools'; Outcome='Agent 能在限定工作区安全读取、搜索、修改并验证代码。'; Checkpoint='05-coding-tools'; Lessons=@(
        @('L17','UTF-8文件读取与路径边界','如何读取仓库文件但不能逃出工作区？','路径必须先 resolve，再验证仍相对于 workspace；文本按严格 UTF-8 读取并限制长度。','实现 read_file 与越界拒绝','python demo.py','outside=blocked'),
        @('L18','仓库搜索与结果限制','搜索整个仓库怎样避免噪声和上下文爆炸？','搜索必须限定目录、glob、文件类型和最大结果，并跳过二进制与 .git。','实现 search_files 和稳定行号输出','python demo.py','matches=1'),
        @('L19','精确补丁与命令验证','Agent 怎样修改代码并证明修改有效？','精确替换在目标缺失或不唯一时失败；命令使用 argv、shell=False，并根据退出码判断成功。','实现 apply_patch 与 run_command','python demo.py','patch=success test_exit=0'),
        @('L20','审批、超时与危险操作','仅在 Prompt 里要求小心为什么不够？','安全由工作区边界、风险级别、执行前审批、命令超时和结构化结果共同保证。','为写入和执行增加审批与超时','python demo.py','denied=denied timeout=timeout')
    )},
    @{ Id='06'; Name='Session上下文与可靠性'; Outcome='支持多轮会话、受控上下文、检查点恢复和分级失败处理。'; Checkpoint='06-session-reliability'; Lessons=@(
        @('L21','Session、Turn与Run','会话历史和一次 Agent 运行为什么不能混为一谈？','Session 跨多轮保存消息，Turn 表示一次用户交互，Run 表示一次 Runtime 生命周期并拥有 run_id。','实现最小 SessionStore','python demo.py','session_messages=2'),
        @('L22','上下文预算与压缩','消息列表无限增长会发生什么？','ContextWindow 根据预算选择本次输入；摘要是有损压缩，必须保留系统约束和最近任务。','实现确定性上下文裁剪','python demo.py','context_trimmed=true'),
        @('L23','Checkpoint与恢复','长任务中断后怎样避免从头重跑？','Checkpoint 只在稳定边界保存恢复状态；有副作用的工具需要幂等键或完成记录。','保存并恢复 next_step 与事件','python demo.py','resumed=true'),
        @('L24','Config、错误、Retry与Timeout','为什么不能遇到所有异常都重试？','配置、协议、暂时性模型错误和工具错误策略不同；只重试明确可恢复错误并设置上限。','加入 RuntimeConfig 和 RetryPolicy','python demo.py','attempts=2 recovered=true')
    )},
    @{ Id='07'; Name='测试评测与可观测性'; Outcome='建立离线测试、20 题协议评测和可追踪故障定位链路。'; Checkpoint='07-testing-evaluation'; Lessons=@(
        @('L25','FakeLLM与单元测试','不调用真实模型怎样测试 Agent 决策链？','FakeLLM 返回预设响应并记录请求，使纯文本、工具调用和异常路径确定可重复。','为 Loop 编写第一个离线测试','python demo.py','unit_tests=passed'),
        @('L26','契约、集成与E2E','单元测试通过为什么项目仍可能失败？','契约测试锁定类型边界，集成测试验证模块协作，E2E 在临时仓库验证真实工具闭环。','完成临时仓库读取、补丁和测试流程','python demo.py','e2e=passed'),
        @('L27','20个任务与回归指标','只看最终答案为什么无法评估 Agent？','评测同时记录成功率、工具调用、步骤、延迟和失败分类，并固定任务与验收器。','运行 20 条离线协议任务','python demo.py','total=20 passed=20'),
        @('L28','Event、Logging与Tracing','失败后怎样知道 Agent 在哪一步出了问题？','Event 服务程序消费，Logging 服务人类阅读，Trace 用 run_id 串联完整运行。','输出可重放 JSONL Trace','python demo.py','trace_events>0')
    )},
    @{ Id='08'; Name='CLI-MCP与作品化'; Outcome='形成可安装、可演示、可答辩的 Coding Agent 作品。'; Checkpoint='08-cli-mcp-final'; Lessons=@(
        @('L29','CLI事件展示与人工审批','Runtime 怎样成为真正可使用的产品？','CLI 消费 Event 展示过程，用 stderr 呈现审批信息，用最终退出码表达运行结果。','运行正式 coding-agent CLI','coding-agent --help','usage: coding-agent'),
        @('L30','MCP到底标准化什么','MCP 与本地 ToolManager 是替代关系吗？','MCP 标准化工具发现与调用传输；业务工具、安全边界和 Runtime 仍由应用负责。','画出 MCP Client、Server 与 Tool 的边界','python demo.py','mcp_transport=stdio'),
        @('L31','用FastMCP暴露只读工具','如何避免 MCP 再实现一套工具逻辑？','MCP adapter 复用 read_file 和 search_files，stdio 模式不能向 stdout 写调试日志。','创建最小 FastMCP server','python demo.py','mcp_server=ready'),
        @('L32','打包发布与最终挑战','怎样证明项目不是只能在作者电脑运行的 Demo？','作品必须可安装、离线测试、可评测、可解释限制，并能从失败 Trace 定位问题。','完成 wheel、README、架构复盘和最终仓库任务','python demo.py','final_project=ready')
    )}
)

function New-LessonDocument($module, $lesson, [string]$nextTitle) {
    $id,$title,$problem,$concept,$change,$command,$expected = $lesson
    $next = if ($nextTitle) { "下一课：$nextTitle" } else { '下一步：完成模块验收与代码答辩。' }
    $official = switch ($id) {
        'L06' { "## 官方核验`n`n- 最后核验日期：2026-07-13`n- [OpenAI Text generation](https://developers.openai.com/api/docs/guides/text)`n- 模型通过 OPENAI_MODEL 显式配置。" }
        'L07' { "## 官方核验`n`n- 最后核验日期：2026-07-13`n- [OpenAI Function calling](https://developers.openai.com/api/docs/guides/function-calling)`n- 模型提出 function_call，Python Runtime 执行工具。" }
        'L08' { "## 官方核验`n`n- 最后核验日期：2026-07-13`n- [OpenAI Function calling](https://developers.openai.com/api/docs/guides/function-calling)`n- function_call_output 使用原 call_id 回传结果。" }
        'L30' { "## 官方核验`n`n- 最后核验日期：2026-07-13`n- [Model Context Protocol](https://modelcontextprotocol.io/)" }
        'L31' { "## 官方核验`n`n- 最后核验日期：2026-07-13`n- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)`n- stdio server 不向 stdout 写调试日志。" }
        default { '' }
    }
    return @"
# $id $title

> 建议时长：60–90 分钟｜讲解 40%｜实践 60%

## 1. 本节要解决的真实问题

$problem

学习完成后，你不仅要记住结论，还要能在运行轨迹和代码中指出它发生在哪里。

## 2. 前置知识回顾

回顾上一课形成的执行链，先写出你认为本节修改前程序缺少的能力。不要先看最终工程代码。

## 3. 场景与类比

把 Coding Agent 想成一名受约束的开发者：它需要知道目标、选择动作、使用工具获得事实，再根据事实继续工作。$problem 这正是本节要补齐的环节。

## 4. 概念图与手工轨迹

~~~text
User Task -> Decide -> Act -> Observe -> Decide Again -> Finish
~~~

先手工写一条输入、动作、观察和下一步，再运行代码验证你的预测。

## 5. 本节唯一核心概念

$concept

本节先把这一件事做正确，不提前加入后续模块的抽象。

## 6. 本节代码增量

修改目标：**$change**。

~~~python
# before: 程序还不能表达本节能力
# after: 只加入本节所需的最小状态与行为
~~~

从上一检查点复制代码到 .learning/current/，只完成上述增量。

## 7. 关键代码解释

阅读代码时依次回答：输入从哪里来、谁做决定、谁执行动作、结果保存在哪里、什么条件结束。任何无法回答的问题都应先通过打印轨迹或测试验证，而不是靠猜测。

## 8. 运行与预期输出

~~~powershell
cd agent-from-scratch/.learning/current
$command
~~~

预期关键输出：

~~~text
$expected
~~~

## 9. 常见错误与排障

- 一次加入多个后续能力，导致无法判断哪一步出错。
- 只看最终文字，没有检查动作、观察和结束条件。
- 运行目录错误，实际执行了最终参考项目而不是学习副本。

排障顺序：确认输入 -> 打印本轮状态 -> 检查动作结果 -> 检查终止条件。

## 10. 实践任务

基础实验：完成“$change”，并保存一段真实运行输出。

进阶挑战：更换一个输入或失败条件，预测轨迹后再运行验证。

## 11. 自测问题

1. $problem
2. 本节概念在执行轨迹的哪一步出现？
3. 如果删除本节代码，用户会观察到什么差异？
4. 本节能力为什么不能只依赖 Prompt 保证？
5. 你会用哪个最小测试证明实现正确？

## 12. 总结与衔接

用三句话复述：本节问题、核心概念、代码变化。$next

## 学习导航

- [课程首页](../../README.md)
- 模块检查点：agent-from-scratch/course-checkpoints/$($module.Checkpoint)/

$official
"@
}

foreach ($module in $modules) {
    $moduleDir = Join-Path $mainRoot ("模块{0}-{1}" -f $module.Id,$module.Name)
    $lessonLinks = @()
    for ($index=0; $index -lt $module.Lessons.Count; $index++) {
        $lesson = $module.Lessons[$index]
        $fileName = "$($lesson[0])-$($lesson[1]).md"
        $lessonLinks += "- [$($lesson[0]) $($lesson[1])]($fileName)"
        $next = if ($index -lt 3) { "$($module.Lessons[$index+1][0]) $($module.Lessons[$index+1][1])" } else { $null }
        Write-Utf8 (Join-Path $moduleDir $fileName) (New-LessonDocument $module $lesson $next)
    }
    $guide = @"
# 模块 $($module.Id) $($module.Name) 导学

## 模块定位

$($module.Outcome)

本模块包含 4 节课，每节 60–90 分钟。请从上一检查点复制学习副本，按顺序完成，不要直接从最终 src/ 抄答案。

## 学习顺序

$($lessonLinks -join "`n")

## 代码起点

- 本模块完成态：agent-from-scratch/course-checkpoints/$($module.Checkpoint)/
- 个人练习目录：agent-from-scratch/.learning/current/

## 模块完成标准

- 能运行模块检查点并解释关键输出。
- 能从空白纸画出本模块新增的数据流。
- 能完成一次故障注入和定位。
- 通过 [模块验收与面试](模块验收与面试.md)。

[返回课程首页](../../README.md)
"@
    Write-Utf8 (Join-Path $moduleDir '模块导学.md') $guide
    $acceptance = @"
# 模块 $($module.Id) $($module.Name) 验收与面试

## 项目验收

- 模块结果：$($module.Outcome)
- 检查点能够完全离线运行。
- 4 节课的基础实验都有运行记录。
- 学习者能指出本模块新增代码，而不是只复述文档。

## 自动验证

~~~powershell
cd agent-from-scratch/course-checkpoints/$($module.Checkpoint)
python demo.py
~~~

## 代码讲解

用 5–10 分钟从用户输入开始，讲到最终输出。必须说明状态在哪里变化、失败如何表达、为什么没有提前加入下一模块抽象。

## 故障分析

主动破坏一个输入、工具结果或结束条件，先根据轨迹定位，再恢复代码并重复验证。

## 设计取舍

比较当前教学实现和最终 src/agent_from_scratch/ 的差异，说明当前简化是为了学习顺序，还是正式架构选择。

## 精选面试题

1. 本模块解决的核心工程问题是什么？
2. 最重要的职责边界在哪里？
3. 哪个失败路径最容易被忽略？
4. 如何离线证明实现正确？
5. 如果用于生产，还缺少哪些能力？

## 通过标准

项目可运行、原理能复述、代码能讲解、故障能定位，四项必须同时满足。

[返回模块导学](模块导学.md)
"@
    Write-Utf8 (Join-Path $moduleDir '模块验收与面试.md') $acceptance
}

$optionalModules = @(
    @{ Dir='RAG'; Title='RAG与外部知识'; Lessons=@(
        @('R01','外部知识与无RAG基线','Agent 失败真的是因为缺少 RAG 吗？','先用固定任务证明外部知识缺失是主要失败源，再决定引入检索。'),
        @('R02','切分、索引与最小检索','文档怎样变成可检索单元？','切分保留语义和元数据，检索返回有限、可追溯的候选片段。'),
        @('R03','RAG Tool与来源安全','检索内容怎样安全进入 Agent？','检索结果通过 ToolResult 注入，并标注来源且不能覆盖系统指令。'),
        @('R04','检索评测与三层边界','RAG、Session、Memory 如何分工？','Session 保存交互，Memory 保存选择后的长期信息，RAG 按问题检索外部知识。')
    )},
    @{ Dir='Multi-Agent'; Title='多Agent工程'; Lessons=@(
        @('A01','可拆分性审计','什么时候不应该拆成多个 Agent？','只有子任务边界、独立评测和权限隔离明确时才值得拆分。'),
        @('A02','Planner-Executor-Reviewer协议','三个角色怎样避免只靠自然语言协作？','角色之间使用稳定输入输出协议，并限制责任和工具权限。'),
        @('A03','共享状态、成本与局部失败','多 Agent 为什么更难调试？','通信、共享状态、重复副作用和局部重试都需要明确所有权。'),
        @('A04','最小Reviewer实验','怎样证明多 Agent 比单 Agent 更好？','只增加可替换 Reviewer，并与单 Agent 基线比较成功率、成本和失败归因。')
    )}
)

foreach ($module in $optionalModules) {
    $dir = Join-Path $optionalRoot $module.Dir
    $links = @()
    foreach ($lesson in $module.Lessons) {
        $id,$title,$problem,$concept = $lesson
        $file = "$id-$title.md"
        $links += "- [$id $title]($file)"
        $content = @"
# $id $title

> 选修课｜建议时长：60–90 分钟｜先完成 32 节主线中的相关基线。

## 1. 本节要解决的真实问题

$problem

## 2. 前置基线

先运行 python -m pytest -q 和 coding-agent-eval，保存单 Agent 基线；没有基线就不能证明扩展有效。

## 3. 场景与概念图

~~~text
Baseline -> Add One Capability -> Measure -> Compare -> Keep or Revert
~~~

## 4. 唯一核心概念

$concept

## 5. 最小代码实验

只增加本课所需 adapter 或角色，不改写核心 Runner 协议。先写失败测试，再实现最小能力。

## 6. 运行与预期输出

~~~powershell
cd agent-from-scratch
python -m pytest -q
coding-agent-eval
~~~

预期：主线测试保持通过，并产生一份扩展前后可比较的指标记录。

## 7. 常见错误

- 没有单 Agent 基线就宣称架构升级。
- 同时改变模型、Prompt、任务集和实现，无法归因结果。
- 把实验性扩展耦合进核心 Runtime。

## 8. 实践任务

基础：完成一个无副作用最小实验。进阶：设计一个能推翻该方案的反例任务。

## 9. 自测问题

1. $problem
2. 进入本实验的硬条件是什么？
3. 新增能力改变了哪个边界？
4. 如何量化收益和成本？
5. 什么结果出现时应该回退？

## 10. 总结

扩展能力必须服务于已证明的问题，而不是为了增加技术名词。

[返回选修导学](模块导学.md)
"@
        Write-Utf8 (Join-Path $dir $file) $content
    }
    Write-Utf8 (Join-Path $dir '模块导学.md') @"
# $($module.Title) 选修模块导学

## 进入条件

完成 32 节主线、保留单 Agent 测试与评测基线，并能够解释核心 Runtime 协议。

## 课程

$($links -join "`n")

## 学习原则

每次只引入一个扩展变量，必须与基线比较；无法归因时不进入正式项目。

[返回课程首页](../../README.md)
"@
    Write-Utf8 (Join-Path $dir '模块验收与面试.md') @"
# $($module.Title) 选修验收与面试

## 验收

- 4 个实验都有基线、变更、指标和结论。
- python -m pytest -q 保持通过。
- 能说明为什么保留或回退该扩展。

## 答辩

讲清问题证据、接口边界、失败归因、成本变化和回退方案。只展示成功 Demo 不算通过。

[返回选修导学](模块导学.md)
"@
}

Write-Output 'Course documents generated.'
