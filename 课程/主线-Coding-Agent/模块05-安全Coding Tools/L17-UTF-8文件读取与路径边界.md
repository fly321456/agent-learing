# L17 UTF-8 文件读取与路径边界：能读文件之前，先定义“允许读哪里”

> 建议学习时间：60–90 分钟。本课只实现受控读取，不讨论搜索、写入或命令。

## 1. 本节要解决的真实问题

Coding Agent 的第一个真实能力通常是读文件。最幼稚的实现只有 `Path(path).read_text()`，却把模型生成的路径当成可信输入：`../secrets.txt`、绝对路径、符号链接和超大文件都可能逃离目标仓库或撑爆上下文。中文源码还会暴露默认编码不一致的问题。

本课建立两个不变量：所有路径先相对固定 Workspace 解析，最终真实路径必须仍在 Workspace 内；文本始终按严格 UTF-8 读取，并允许按行与字符预算截断。问题链是：为什么过滤字符串中的 `..` 不够？绝对路径怎么办？Windows 盘符和大小写会怎样？读取成功为何还要限制长度？

## 2. 前置回顾与信任边界

模块 4 已把 ToolCall 交给 ToolManager，但 arguments 仍来自模型，属于不可信输入。模型不是恶意用户才需要防护吗？不是。提示注入、错误推理和模糊任务都可能生成危险路径。安全边界应由代码保证，不能依赖 Instructions 中一句“不要越界”。

```text
Model path (untrusted)
  → workspace_path() resolve + containment check
  → approved absolute Path
  → strict UTF-8 read
  → bounded Observation
```

Workspace 是一次工具运行的环境，不是全局当前目录的别名。

## 3. 类比与两个具体案例

把 Workspace 想成实验室门禁区域。访客写“隔壁房间”并不会改变门禁权限；管理员先把描述换成真实房间号，再检查是否属于授权楼层。

案例一：Workspace 为 `D:/repo`，请求 `src/app.py`，解析后仍在 `D:/repo/src/app.py`，允许。案例二：请求 `../credentials.txt`，规范化后成为 `D:/credentials.txt`，无法相对到 Workspace，拒绝。第三个案例是 `inside/link` 指向仓库外：只做字符串前缀检查会放过，`resolve()` 后再检查才能看到真实目标。

## 4. 概念推导：解析与包含关系

```python
def workspace_path(context, path):
    target = (context.workspace / path).resolve()
    try:
        target.relative_to(context.workspace)
    except ValueError as exc:
        raise WorkspaceBoundaryError(...) from exc
    return target
```

不要写 `str(target).startswith(str(workspace))`：`D:/repo-old` 也以 `D:/repo` 开头，大小写和分隔符还会制造差异。Path 的结构关系才表达目录包含。

`ToolContext.__post_init__` 先把 Workspace 自身 resolve，保证后续比较双方处于同一规范形态。

## 5. 本课唯一代码增量：受控 read_file

```python
def read_file(*, context, path, start_line=1, end_line=None, max_chars=20_000):
    target = workspace_path(context, path)
    text = target.read_text(encoding="utf-8", errors="strict")
    selected = "".join(text.splitlines(keepends=True)[start_line - 1:end_line])
    return selected[:max_chars] if len(selected) > max_chars else selected
```

源码见 [core.py](../../../agent-from-scratch/course-checkpoints/05-coding-tools/src/course_tools/core.py)。保留换行让行级内容接近原文件；`start_line` 使用人类习惯的 1 起始；无效范围立即报错。

## 6. 两个错误直觉与纠正

### 误区一：删掉 `..` 就安全

绝对路径、符号链接和编码后的路径仍可能逃逸，字符串替换还会破坏合法文件名。正确顺序是解析真实路径，再验证包含关系。

### 误区二：读取工具没有副作用，所以无需限制

读取不会改文件，却可能泄露工作区外信息，也会把数 MB 内容塞入上下文。权限风险和资源风险都存在。只读不等于无限制。

另一个误区是遇到非法 UTF-8 自动 `errors="ignore"`。静默丢字节会让 Agent 基于损坏源码修改，严格失败更可解释。

## 7. 完整运行轨迹

```text
workspace=<temp>
write 说明.md as UTF-8: 第一行 / 第二行
read_file(path=说明.md, start_line=2)
  → resolved inside workspace
  → strict decode
  → Observation "第二行\n"
read_file(path=../outside.md)
  → resolved outside
  → WorkspaceBoundaryError
```

边界错误最终由 ToolManager 转为 status=error，而不是让模型直接获得 Python Path 对象。

## 8. 修改前后差异

修改前：

```python
text = Path(path).read_text()
```

修改后：

```python
context = ToolContext(workspace)
text = read_file(context=context, path="src/app.py", max_chars=20_000)
```

多出来的 Context 不是仪式，它把授权根目录显式传入，测试可以使用临时目录，不依赖开发者机器当前 cwd。

## 9. 关键边界与失败语义

文件不存在、目录误当文件、非法 UTF-8、越界路径和无效行号是不同根因，但本课先让 ToolManager 统一为可观察 error，并保留具体 error 文本。模块 7 才系统设计错误分类指标。

截断应带明显标记：

```text
... [truncated]
```

否则模型可能把不完整函数误认为文件结尾。读取范围和最大字符应同时存在：行范围服务定位，字符上限服务资源预算。

## 10. 运行、预期输出与故障实验

```powershell
python agent-from-scratch/course-checkpoints/05-coding-tools/steps/l17_read_boundary.py
```

```text
utf8=ok
outside=blocked
```

故障实验：改用默认编码读取中文；把 `relative_to` 替换成 startswith；创建超长文件观察截断；传 `start_line=0`；在支持符号链接的环境创建指向外部的 link。每次都说明失败发生在哪一层。

## 11. 基础练习与进阶挑战

基础练习：读取第 2–3 行并验证保留换行；设置 `max_chars=5` 检查截断标记。进阶挑战：设计允许多个只读根目录的 Context，说明它与“任意绝对路径白名单”相比如何审计。

答案见 [模块练习参考答案](模块练习参考答案.md)。

## 12. 自测、总结与下一课

1. 为什么检查字符串中是否有 `..` 不够？
2. 为什么必须先 resolve 再验证包含关系？
3. 只读 Tool 有哪些安全与资源风险？
4. 为什么非法 UTF-8 不应静默 ignore？
5. 行范围和字符预算分别解决什么问题？

下一课 [L18 仓库搜索与结果限制](L18-仓库搜索与结果限制.md) 将在同一 Workspace 边界内扩大观察范围，同时防止搜索结果淹没上下文。
