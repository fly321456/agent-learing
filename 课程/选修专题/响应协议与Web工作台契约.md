# 选修：响应协议与 Web 工作台契约

## 定位

本专题承接原“Agent 结构化输出与前端工作台”内容，但不属于主线必修。主线 M04 只保证 Runtime 协议与 CLI 消费；前端工作台必须在真实实现时再引入 UI 类型。

## 进入条件

- M04 的 Event 顺序与 `RunResult` 已稳定。
- CLI 已能展示工具过程和最终结果。
- 已明确工作台用户、任务流程和持久化需求。
- 已选择 SSE、WebSocket 或轮询，并说明断线恢复语义。

## 最小契约

前端应消费稳定 Event 和最终 RunResult，不读取 OpenAI 原始对象。传输层可增加游标、心跳和连接状态，但不得反向污染核心 Runtime。

`Block` 只在前端确实需要渲染文本、工具、审批或错误卡片时引入，并放在 adapter 层。没有实现 Web 时，不在核心 Schema 里提前维护空字段。

## 实验产物

1. 一份 Event 到 UI 状态的映射表。
2. 一个断线重连与事件去重方案。
3. 一个工具审批交互原型及后端校验流程。
4. 前后端契约测试。

## 验收

先运行主线协议测试：

```powershell
cd agent-from-scratch
python -m pytest -q tests/test_runner.py tests/test_cli.py
```

只有真实前端、传输层和契约测试都存在时，才能把专题状态改为“已实现”。当前状态：课程设计已完成，Web 产品未实现。

## 官方核验

- 最后核验日期：2026-07-13
- [Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs)

