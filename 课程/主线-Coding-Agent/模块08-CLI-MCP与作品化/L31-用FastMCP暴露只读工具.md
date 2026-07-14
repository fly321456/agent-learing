# L31 用 FastMCP 暴露只读工具：先共享最小能力，再讨论远程副作用

> 建议学习时间：60–90 分钟。最后核验日期：2026-07-14；示例针对官方 MCP Python SDK v1.27.x。

## 1. 本节要解决的真实问题

理解协议边界后，本课实现最小 MCP Server。最容易展示的做法是把 read、search、patch、command 全注册，但这会把模块 5 的审批与执行风险跨进程扩散，也让初学者误以为 MCP 暴露越多越好。

我们只共享两个只读 Tool：`read_workspace_file` 和 `search_workspace`。Server 固定一个 Workspace，路径必须 resolve 后仍位于其中，文本严格 UTF-8，搜索有结果上限。测试通过 `server.list_tools()` 检查名称集合，不能只看源码“似乎没有写工具”。

问题链是：装饰器如何生成 Schema？闭包中的 Workspace 是否会被客户端覆盖？为何不暴露任意 path 根目录？Tool docstring 有什么作用？如何测试 Server 而不启动永不退出的 stdio 进程？

## 2. FastMCP 最小结构

官方 v1.x 用法是创建 `FastMCP`，用 `@server.tool()` 或 `server.tool()(function)` 注册函数，再调用 `server.run()`。直接运行默认使用 stdio。

```python
from mcp.server.fastmcp import FastMCP

server = FastMCP("Course Read-Only Coding Tools")

@server.tool()
def read_workspace_file(path: str) -> str:
    """Read UTF-8 text inside the configured workspace."""
    ...
```

类型注解和 docstring 帮助 SDK 生成 Tool Schema。它们是模型可见接口的一部分，应清晰描述范围和结果。

## 3. 为什么先做本地纯函数

课程先实现 `create_read_only_tools(workspace)` 返回普通 Python callable，再把它们注册到 FastMCP：

```text
pure workspace functions
  → unit tests: path / UTF-8 / result limit
  → FastMCP registration
  → MCP discovery test
```

这样路径安全不依赖启动协议进程，失败定位更快。FastMCP 层只负责 Schema 与调用适配，不重新实现读取逻辑。

案例一：普通函数读取临时 README，证明输出正确。案例二：相同函数传 `../outside.md`，在到达 SDK 之前就抛边界错误。

## 4. Workspace 闭包与路径边界

```python
root = Path(workspace).resolve()

def read_workspace_file(path: str, start_line: int = 1, end_line: int | None = None):
    target = _workspace_path(root, path)
    text = target.read_text(encoding="utf-8", errors="strict")
    return "".join(text.splitlines(keepends=True)[start_line - 1:end_line])
```

root 由 Server 启动者决定，不作为 Tool 参数暴露。客户端只能提供相对 path，不能把 Workspace 改为系统根目录。`_workspace_path` 与模块 5 使用相同 resolve + relative_to 原则。

只读仍有数据泄露风险，因此部署者必须选择正确 Workspace，不能默认把用户主目录作为根。

## 5. 本课唯一代码增量：注册两个 Tool

```python
def create_mcp_server(workspace):
    tools = create_read_only_tools(workspace)
    server = FastMCP("Course Read-Only Coding Tools")
    server.tool()(tools["read_workspace_file"])
    server.tool()(tools["search_workspace"])
    return server
```

Tool 名来自函数 `__name__`，测试期望恰好是两个稳定名称。若重构函数名，MCP 公共接口也会变化，应视为 API 变更。

模块最终项目中的 Server 同样复用正式 `read_file` 与 `search_files`，不复制一套不同安全规则。

## 6. Search Tool 的输出预算

```python
def search_workspace(query, path=".", glob="*", max_results=50):
    ...
    if len(matches) >= max_results:
        return "\n".join(matches) + "\n... [result limit reached]"
```

远端 Tool 也要限制输出。MCP 能传输大结果不代表模型 Context 能合理消费。返回相对路径、行号和片段，跳过 `.git` 与二进制，并明确截断。

Server 端设置硬上限更安全；客户端传入的 max_results 还应限制最大值，教学版将这一点留作挑战。

## 7. 两个错误直觉与纠正

### 误区一：只读 Tool 可以访问整个磁盘

读取不会修改文件，却可能泄露密钥、配置和私人数据。Workspace 仍是必需授权边界，远程部署还需要认证与审计。

### 误区二：函数注册成功就算 MCP 验收完成

装饰器可能改名、漏注册或意外注册第三个 Tool。应调用 SDK 的 `list_tools()`，从客户端可见视角断言集合。

另一个误区是直接启动 stdio 做普通单元测试。Server 会等待输入，测试容易挂起；能力发现可直接异步调用，真正 Transport 只需少量集成测试。

## 8. 完整发现与调用轨迹

```text
create temp workspace
create_mcp_server(workspace)
await server.list_tools()
  → read_workspace_file
  → search_workspace
assert no apply_patch / run_command

client call read_workspace_file(path=README.md)
server resolves path inside root
server returns UTF-8 text
```

边界测试再调用 `../outside.md`，确认拒绝发生在 Server，而不是依赖 Client 自律。

## 9. 为什么不暴露写 Tool

跨进程写入需要更复杂协议：审批请求如何到达用户？Server 是否允许 Client 声称“已审批”？中断后副作用如何幂等？多客户端是否共享 Workspace？审计记录存哪边？

```text
read-only MCP: bounded observation
write MCP: identity + authorization + approval + idempotency + audit
```

在这些问题未回答前，保持只读不是功能不足，而是正确的最小安全边界。CLI 仍可使用本地受审批 Patch/Command。

## 10. 运行、预期输出与故障实验

```powershell
python agent-from-scratch/course-checkpoints/08-cli-mcp-final/steps/l31_fastmcp_read_only.py
```

```text
transport=stdio tools=read_workspace_file,search_workspace
```

故障实验：注册第三个 write Tool，确认集合测试失败；请求越界路径；写入二进制文件并搜索；给 max_results 极大值分析硬上限；在 stdio Server 中普通 print，说明协议污染风险。

## 11. 基础练习与进阶挑战

基础练习：使用 `list_tools()` 打印每个 Tool 的输入 Schema，并检查 path 类型。进阶挑战：为 max_results 增加服务端最大值 100，为单行增加 max_chars，并写异步调用测试。

答案见 [模块练习参考答案](模块练习参考答案.md)。

## 12. 自测、总结与下一课

1. 为什么先实现普通函数再注册 FastMCP？
2. Workspace 为什么不能由 Tool 参数覆盖？
3. 如何从客户端视角证明只有两个 Tool？
4. 只读 Server 仍有哪些安全风险？
5. 暴露写 Tool 前必须解决哪些协议问题？

下一课 [L32 打包发布与最终挑战](L32-打包发布与最终挑战.md) 将把检查点构建为 wheel，并形成可克隆、可运行、可测试、可答辩的最终作品。

官方来源：[MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)。
