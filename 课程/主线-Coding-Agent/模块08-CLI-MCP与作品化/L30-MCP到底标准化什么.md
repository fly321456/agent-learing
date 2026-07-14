# L30 MCP 到底标准化什么：连接能力，不替你实现 Agent

> 建议学习时间：60–90 分钟。最后核验日期：2026-07-14；依据官方 MCP Python SDK v1.x 文档。

## 1. 本节要解决的真实问题

项目已有 ToolSpec 和 ToolManager，为什么还需要 MCP（Model Context Protocol，模型上下文协议）？常见宣传把 MCP 描述成“装上就拥有 Agent”或“所有工具自动安全”。这会混淆两层：MCP 让客户端以统一方式发现和调用外部能力；Agent Runtime 仍负责目标、决策、循环、审批、Context、终止和结果。

本课不急着写 Server，先回答协议边界。问题链是：MCP Client 与 Server 分别是谁？Tool Schema 如何被发现？stdio 是什么？MCP 是否决定模型何时调用 Tool？远程 Server 的结果可信吗？审批应放在客户端、服务端还是两边？

## 2. 没有 MCP 时的集成成本

```text
Agent A → custom Python function
Agent B → custom HTTP wrapper
IDE C   → another plugin format
```

每个宿主都要重新定义工具名称、参数、调用和结果。MCP 提供统一 Client–Server 协议，使 Server 可以公开 Tools、Resources、Prompts 等能力，客户端通过协商和消息调用。

它标准化连接方式，不保证每个 Tool 设计优秀，也不保证返回事实正确。

## 3. 一致类比与两个案例

MCP 像 USB 接口：插头、电气协议和设备发现统一，但 USB 不决定用户何时打印、不审查文档内容，也不保证设备无恶意。

案例一：只读仓库 Server 暴露 `read_workspace_file` 与 `search_workspace`。不同 MCP Client 都能发现相同名称和参数。案例二：一个天气 Server 返回错误温度，协议调用仍可能“成功”；MCP 成功表示通信和 Tool 执行完成，不表示业务事实正确。

第三个安全案例：Server 声称 Tool 叫 `read_file`，实际有副作用。客户端必须把远端描述视为不可信输入，服务端也必须自己执行权限边界。

## 4. MCP 标准化的内容

```text
能力发现：有哪些 Tools / Resources / Prompts
Schema：Tool 名称、描述、输入结构
调用：客户端如何发请求、服务端如何返回结果或错误
Transport：stdio、Streamable HTTP 等消息承载
Lifecycle：初始化、能力协商和会话通信
```

本课程只实现 Tool Server 的最小子集。Resources 与 Prompts 值得后续扩展，但不应为了展示术语一次全加。

官方 Python SDK v1.x 提供 `FastMCP` 简化 Server 声明，v2 在当前核验时仍未稳定，因此项目依赖保留 `mcp>=1.27,<2`。

## 5. MCP 不标准化的内容

```text
Agent 目标和 Instructions
何时选择哪个 Tool
Agent Loop 与 max_steps
业务成功判定
工作区授权和人工审批策略
Session / Checkpoint / Retry
工具内容真实性与安全性
```

这些仍属于 Runtime 和应用。把 Tool 接入 MCP 后，原有 ToolManager 的边界不会自动消失；只是调用从本地函数变为协议请求。

## 6. stdio Transport 的运行模型

stdio 模式通常由 Client 启动 Server 子进程，通过标准输入/输出交换协议消息。Server 的 stdout 属于协议通道，不能随意 `print("debug")`，否则可能破坏消息；诊断应写 stderr 或使用协议 Logging。

```text
Client process
  ├─ starts: python -m course_product
  ├─ writes MCP messages → server stdin
  └─ reads MCP messages  ← server stdout
```

stdio 适合本地工具和最小作品。远程部署可用 Streamable HTTP，但会增加认证、网络暴露和部署治理，本课程不把它当必修。

## 7. 两个错误直觉与纠正

### 误区一：MCP Server 就是一个 Agent

Server 提供能力，不负责围绕用户目标多轮决策。Agent Client 可以调用它，普通程序也可以调用它。没有 Loop 的 Server 仍是 MCP Server，不是 Agent。

### 误区二：接入 MCP 后 Tool 自动安全

协议不替应用定义 Workspace、审批和数据脱敏。Server 必须执行自己的访问边界，Client 也应根据风险确认调用。双边防护并不重复，因为两边信任域不同。

另一个误区是 MCP 取代内部 ToolSpec。客户端适配器仍需把远端 Tool Schema 转换为 Runtime 可消费的形式，并把结果标准化为 ToolResult。

## 8. 一次 Tool 调用轨迹

```text
Client initialize → Server capabilities
Client list_tools
Server returns read_workspace_file(path,start_line,end_line)
Agent Runtime chooses Tool
Client call_tool(arguments={path:"README.md"})
Server validates Workspace and reads UTF-8
Server returns text result
Client converts result to Observation / ToolResult
Runner continues Loop
```

协议每一步成功仍不能证明最终 Task 完成；完成由 RunResult 和评测判定。

## 9. MCP 与课程 Runtime 的映射

本地 ToolSpec 的 name/description/parameters 对应远端 Tool Schema；ToolManager.execute 可扩展为 MCP Client 调用；ToolResult 保存成功、错误、拒绝或超时；Event 记录远程调用顺序。

```text
MCP Tool result → adapter normalization → ToolResult → Event → next LLM call
```

不要让 Runner 直接处理 MCP SDK 原始对象，这与 L14 禁止读取供应商 raw response 是同一架构原则：外部协议在适配层结束。

## 10. 运行、预期输出与故障实验

```powershell
python agent-from-scratch/course-checkpoints/08-cli-mcp-final/steps/l30_mcp_boundaries.py
```

```text
mcp_standardizes=discovery,schemas,invocation,results,transports
mcp_does_not_standardize=agent_policy,approval,task_success
```

故障实验：把 Server stdout 加一条普通 print，分析 stdio 风险；假设远端 Tool 描述错误，列出客户端防护；把 max_steps 误放进 Server，讨论多客户端为何冲突；比较本地 Tool exception 与 MCP error 的标准化位置。

## 11. 基础练习与进阶挑战

基础练习：画出 Runtime、MCP Client、MCP Server、Workspace 四层图，并标注信任边界。进阶挑战：设计一个 MCP Tool Adapter 接口，只写输入输出契约，不真正联网；说明 cancellation、timeout 和 approval 放在哪里。

答案见 [模块练习参考答案](模块练习参考答案.md)。

## 12. 自测、总结与下一课

1. MCP 标准化哪些连接问题？
2. MCP 为什么不等于 Agent Runtime？
3. stdio Server 为什么不能随意写 stdout？
4. Tool 安全为何需要客户端和服务端共同负责？
5. MCP SDK 原始结果为什么应停在 Adapter？

下一课 [L31 用 FastMCP 暴露只读工具](L31-用FastMCP暴露只读工具.md) 将按这条边界实现最小 Server，并用 SDK 自省证明只有两个只读 Tool。

官方来源：[MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)。
