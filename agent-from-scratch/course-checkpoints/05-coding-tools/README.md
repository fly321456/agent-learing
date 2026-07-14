# 05 Safe Coding Tools

模块 5 的独立离线快照，覆盖 UTF-8 文件读取、工作区边界、受限搜索、唯一精确补丁、argv 命令、审批、非零退出码和超时。

```powershell
python demo.py
python steps/l17_read_boundary.py
python steps/l18_search_limits.py
python steps/l19_patch_and_verify.py
python steps/l20_approval_and_timeout.py
```

Demo 预期输出包含 `outside=blocked`、`patch=success` 和 `test=success`。所有写入及命令默认需要审批；没有回调时按拒绝处理。命令使用 `shell=False`，路径必须解析在临时工作区内。
