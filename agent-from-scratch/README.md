# agent-from-scratch

这是课程主项目的当前正式入口。

从现在开始，这个目录里无后缀的文件是唯一主线：

- `app.py`
- `agent.py`
- `runner.py`
- `llm.py`
- `config.py`
- `prompts.py`
- `tools.py`
- `schemas.py`

## 当前状态

目前这个项目已经完成到：

1. `Agent` 只负责保存配置
2. `Runner` 已经具备最小 tool-calling 闭环
3. `BaseLLM / OpenAILLM` 已经建立抽象层
4. `tools.py` 已经接入第一个真实 Tool：`get_current_time`
5. `schemas.py` 已经定义第一个真实 Tool Schema
6. `app.py` 已经能作为当前主入口

## 后续开发原则

1. 后续课程和项目实现，优先继续修改无后缀主线文件。
2. `*_lesson*.py` 这类文件视为历史练习快照，不再作为默认入口继续扩展。
3. 如果后面需要新增能力，优先往 `runner.py`、`tools.py`、`schemas.py`、`prompts.py` 这些正式文件里演进。

## 当前运行方式

在配置好 `OPENAI_API_KEY` 后，可直接运行：

```bash
python app.py
```

默认演示问题：

```text
What time is it now?
```

## 下一步最合理的演进

1. 新增第二个 Tool，例如 `read_file`
2. 给 `Runner` 增加多 Tool 路由和更清晰的错误处理
3. 把打印式输出升级为结构化 Result
4. 增加最小测试，验证 Tool Call 闭环
