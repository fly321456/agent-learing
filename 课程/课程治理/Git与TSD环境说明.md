# Git 与 TSD 环境说明

## 当前状态

本机 Windows 企业安全策略加载了 `TsdEncrypt` 与 `TsdEncryptMF` 文件保护驱动。Python、编辑器和 PowerShell 能读取正常源码，但 Git 读取以下 8 个历史文件时得到约 8192 字节的 `%TSD-Header-###%` 保护容器，因此产生虚假二进制修改：

- `agent-from-scratch/agent.py`
- `agent-from-scratch/app.py`
- `agent-from-scratch/config.py`
- `agent-from-scratch/llm.py`
- `agent-from-scratch/prompts.py`
- `agent-from-scratch/runner.py`
- `agent-from-scratch/schemas.py`
- `agent-from-scratch/tools.py`

这些旧根文件不是正式入口，本轮也没有主动编辑。2026-07-17 复核又确认：正式 `agent-from-scratch/src/agent_from_scratch/runner.py`、`tools.py` 等已编辑源码对 Python 仍是正确明文，但 Git 的 `diff --numstat` 同样返回二进制 `- -`。因此影响范围已经不再局限于上述 8 个旧文件；不能继续宣称正式 `src/` 可安全显示或暂存文本 diff。

## 安全禁令

- 不要执行 `git add -A`，也不要暂存任何被 `git diff --numstat` 报为 `- -` 的文件。
- 不要为了消除状态而覆盖、批量移动或重写旧文件。
- 不要停止、卸载或绕过企业安全驱动。
- 不要把 Git 读到的 8192 字节容器当作源码保存。

## 推荐处理

优先请安全管理员将仓库目录或开发工具 Git 进程加入合规白名单。若企业策略允许，也可以把仓库克隆到明确的非保护开发目录，再从版本库重新检出旧文件。迁移前应确认目标路径属于批准的开发区域。

## 恢复验收

安全策略调整后执行：

```powershell
git status --short
git diff --text -- agent-from-scratch/llm.py
git diff --numstat -- agent-from-scratch/llm.py
git diff --numstat -- agent-from-scratch/src/agent_from_scratch/tools.py
```

验收标准：8 个旧文件不再显示虚假修改；所有待提交的正式源码在 `git diff --numstat` 中都显示数字行数而不是二进制 `- -`；Git diff 与 Python/PowerShell 读取的明文一致。随后才能安全暂存正式源码，是否移动旧根脚本仍需单独审批。

## 本次重构策略

本次没有修改或移动这 8 个旧文件。新 Runtime 实现位于标准 `src/` 包，并已通过 Python 明文视角的测试和 wheel 隔离安装验证；但 Git 视角仍可能是保护容器。本轮禁止暂存或提交，直到安全管理员解除策略并按上面的恢复验收确认每个目标文件都是正常文本。
