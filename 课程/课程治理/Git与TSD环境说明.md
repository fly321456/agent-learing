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

这些文件的 Python 明文哈希与当前 HEAD 一致，不是本次重构产生的真实内容修改。正式新代码位于 `agent-from-scratch/src/agent_from_scratch/`，Git 可以正常显示其文本 diff。

## 安全禁令

- 不要执行 `git add -A` 或提交上述 8 个文件。
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
```

验收标准：8 个旧文件不再显示虚假修改；`git diff --numstat` 不再以二进制 `- -` 表示；Git 显示的是正常 Python 文本。随后才能安全地移动或删除旧根脚本。

## 本次重构策略

本次没有修改或移动这 8 个旧文件。所有新 Runtime 实现放入标准 `src/` 包，并通过普通 wheel 隔离安装验证。提交时必须显式选择新代码、课程归档和文档，直到 TSD 问题由外部策略解除。

