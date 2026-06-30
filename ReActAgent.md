# ReActAgent.py 代码解析

这是一个基于 **ReAct（Reasoning + Acting）范式** 的智能体实现，核心思想是让模型通过"思考→行动→观察"的循环来解决复杂任务。

---

## 1. 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    ReAct Agent 主循环                       │
├─────────────────────────────────────────────────────────────┤
│  RUN (入口)                                                 │
│    ↓                                                        │
│  [加载状态] ←─────────────────────┐                         │
│    ↓                              │                         │
│  OBSERVE → THINK → ACT            │                         │
│    ↓                              │                         │
│  [保存状态到本地] ────────────────┘                         │
│    ↓                                                        │
│  [循环直到完成或达到最大步数]                                │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 类与方法详解

### 2.1 构造函数 `__init__`

```python
def __init__(self, tools: dict, state_file: str = "agent_state.json"):
    self.tools = tools          # 可用工具字典
    self.state_file = state_file
    self.max_steps = 10         # 防止无限循环
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `tools` | `dict` | 工具注册表，key 为工具名，value 为可调用函数 |
| `state_file` | `str` | 状态持久化文件路径，默认 `agent_state.json` |
| `max_steps` | `int` | 最大执行步数，防止死循环 |

---

### 2.2 `observe` 方法（观察）

```python
def observe(self, state: Dict) -> Dict:
    """观察：整合当前所有信息（用户输入、上一步结果、记忆）"""
    # 这里可以接入你的本地记忆系统（如 SQLite 读取历史）
    return state
```

**设计意图**：收集当前环境信息作为思考的输入。目前是占位实现，实际应用中可扩展：
- 从数据库读取历史对话
- 接入向量数据库检索相关知识
- 读取外部环境状态

---

### 2.3 `think` 方法（思考）

```python
def think(self, state: Dict) -> str:
    """思考：LLM 根据观察决定下一步动作（伪代码）"""
    # 1. 构建 Prompt：描述目标、可用工具、历史
    prompt = f"""
    目标：{state['goal']}
    可用工具：{list(self.tools.keys())}
    历史步骤：{state.get('history', [])[-3:]}  # 最近3步
    请决定下一步动作（格式：tool_name 或 FINISH）：
    """
    # 2. 调用 LLM（此处简化）
    if "未完成" in state.get('last_result', ''):
        return "continue_processing"
    return "FINISH"
```

**核心逻辑**：
1. **Prompt 构建**：包含目标、可用工具列表、最近 3 步历史
2. **LLM 决策**：返回 `tool_name`（调用工具）或 `FINISH`（完成任务）
3. **简化实现**：当前用规则模拟 LLM，实际应接入真实大模型 API

**关键技巧**：`state.get('history', [])[-3:]` 只保留最近 3 步，避免 Prompt 过长。

---

### 2.4 `act` 方法（行动）

```python
def act(self, action: str, state: Dict) -> Dict:
    """执行：调用工具并更新状态"""
    if action == "FINISH":
        state['status'] = 'completed'
        return state
    
    tool = self.tools.get(action)
    if tool:
        result = tool(state.get('data'))
        state['last_result'] = result
        state['history'].append(f"执行 {action}: {result}")
    
    return state
```

**执行流程**：
1. 判断是否为 `FINISH`，若是则标记完成
2. 从工具字典中查找并调用对应工具
3. 更新状态：记录工具返回结果、追加历史记录

---

### 2.5 `run` 方法（主循环）

```python
def run(self, initial_goal: str):
    """运行主循环（支持断点续跑）"""
    # 尝试从本地文件加载状态（实现持久化）
    try:
        with open(self.state_file, 'r') as f:
            state = json.load(f)
        print("检测到历史状态，恢复运行...")
    except FileNotFoundError:
        state = {'goal': initial_goal, 'history': [], 'step': 0}
    
    while state.get('status') != 'completed' and state['step'] < self.max_steps:
        state['step'] += 1
        current_state = self.observe(state)
        action = self.think(current_state)
        print(f"[Step {state['step']}] 决策: {action}")
        state = self.act(action, state)
        # 保存状态到本地（实现 Checkpoint）
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    return state
```

**两大核心特性**：

| 特性 | 实现方式 | 作用 |
|------|----------|------|
| **断点续跑** | 启动时读取 `state_file` | 意外中断后可从上次位置恢复 |
| **Checkpoint** | 每步后写入 `state_file` | 防止进度丢失 |

---

## 3. 使用示例

```python
def my_summarize_tool(text):
    return f"已总结: {text[:100]}..."

agent = ReActAgent(tools={'summarize': my_summarize_tool})
result = agent.run("处理文档并生成报告")
```

注册一个 `summarize` 工具，传入初始目标后启动 agent。

---

## 4. 状态结构

| 字段 | 类型 | 说明 |
|------|------|------|
| `goal` | `str` | 初始目标 |
| `history` | `list` | 执行历史记录 |
| `step` | `int` | 当前步数 |
| `status` | `str` | 状态：`completed` 或未设置 |
| `last_result` | `any` | 上一步工具执行结果 |
| `data` | `any` | 传入工具的输入数据 |

---

## 5. 代码优化建议

当前实现是**简化版框架**，生产环境需完善以下几点：

1. **接入真实 LLM**：`think` 方法需调用 OpenAI/Anthropic 等 API
2. **工具调用参数化**：当前工具只传 `state.get('data')`，应支持更灵活的参数传递
3. **错误处理**：`act` 方法缺少工具不存在或执行失败的异常处理
4. **日志系统**：替换 `print` 为结构化日志
5. **异步支持**：工具调用和状态保存可改为异步操作

---

## 6. 总结

该文件实现了一个**轻量级 ReAct Agent 框架**，核心价值在于：
- **模块化设计**：观察、思考、行动分离，易于扩展
- **持久化机制**：支持断点续跑，生产环境友好
- **防死循环**：`max_steps` 保护机制

适合作为智能体应用的基础框架，后续可根据业务需求扩展工具集和记忆系统。