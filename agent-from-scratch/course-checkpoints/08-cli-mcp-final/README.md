# 08 CLI, MCP And Final Product

模块 8 的独立可打包快照，覆盖 CLI Event 渲染、默认拒绝审批、只读 Workspace Tools、FastMCP stdio Server 和 wheel/editable 安装。

```powershell
python demo.py
python steps/l29_cli_events_approval.py
python steps/l30_mcp_boundaries.py
python steps/l31_fastmcp_read_only.py
python steps/l32_package_release.py
```

MCP 使用官方 Python SDK v1.x 接口，依赖约束为 `mcp>=1.27,<2`。Server 只暴露 `read_workspace_file` 与 `search_workspace`，不暴露 Patch 或 Command。
