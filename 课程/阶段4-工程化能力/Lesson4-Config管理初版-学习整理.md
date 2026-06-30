# Lesson4：Config 管理初版

## 1. 本课目标

这一课我们进入工程化能力里的一个基础模块：

> **配置管理（Config Management）**

前面几课我们已经逐步把 Agent 做成了一个可以运行、可测试、可追踪、可重试的系统。

但是如果配置仍然散落在各处，比如：

- `model="gpt-5"` 写死在 `llm.py`
- `max_turns=10` 写死在 `runner.py`
- `timeout=30` 写死在调用逻辑里
- `OPENAI_API_KEY` 到处直接 `os.getenv()`

那么项目很快就会进入一种很常见的混乱状态：

```text
能跑

但是不好改

不好切环境

不好测试

不好部署
```

所以这一课的目标不是增加一个“新能力”，而是做一次非常重要的工程整理：

> **把“运行参数”从“业务逻辑”里拆出来。**

---

## 2. 为什么 Config 这么重要

很多初学者会觉得配置管理只是小事：

```python
model = "gpt-5"
```

看起来当然能跑。

但真正做 Agent 项目时，你很快会遇到下面这些场景：

### 场景 1：开发环境和生产环境不同

开发环境：

```text
gpt-5-mini
```

生产环境：

```text
gpt-5
```

如果模型写死在代码里，每次切换都要改源码。

---

### 场景 2：不同 Agent 用不同参数

例如：

- Coding Agent：`max_turns = 20`
- Review Agent：`max_turns = 8`
- Search Agent：`timeout = 60`

如果没有统一配置层，这些参数最终都会散落在不同文件中。

---

### 场景 3：测试需要更保守的配置

例如测试时你希望：

- 关闭真实 API
- 使用 mock model
- 降低 timeout
- 缩短 max_turns

这时候配置如果不独立，测试会非常难写。

---

## 3. 这一课要建立的核心认知

以后你看到任何成熟项目，都应该自动有这个判断：

> **凡是“可能变化”的东西，都不应该硬编码在主逻辑里。**

在 Agent 项目里，常见可变项包括：

- 模型名
- API Key
- Base URL
- 超时时间
- 最大循环轮数
- 是否开启 tracing
- 日志级别
- 重试次数

这些内容本质上都属于：

> **运行时配置**

而不是：

> **Agent 核心逻辑**

---

## 4. 先看一个不好的写法

很多新人会这样写：

```python
class OpenAILLM(BaseLLM):
    def generate(self, messages, tools=None):
        response = self.client.responses.create(
            model="gpt-5",
            input=messages,
            tools=tools or [],
            timeout=30,
        )
        return response
```

表面看起来没问题。

但问题是：

- 模型写死了
- timeout 写死了
- tools 默认策略也写死了

这意味着：

> **每次想调整策略，都要改实现代码。**

这会让“配置变更”和“逻辑变更”混在一起。

---

## 5. 更合理的第一版设计

我们这一课先不追求复杂，只做一个最小可维护版本。

项目里新增一个配置对象，例如：

```python
class Settings:
    def __init__(
        self,
        model: str,
        max_turns: int = 10,
        request_timeout: int = 30,
        max_retries: int = 2,
        enable_tracing: bool = True,
        log_level: str = "INFO",
    ):
        self.model = model
        self.max_turns = max_turns
        self.request_timeout = request_timeout
        self.max_retries = max_retries
        self.enable_tracing = enable_tracing
        self.log_level = log_level
```

这一版先解决最重要的问题：

> **让配置成为一个独立对象。**

以后谁需要配置，就显式依赖这个对象，而不是到处自己读取环境变量。

---

## 6. 推荐的职责划分

### `config.py`

负责：

- 读取环境变量
- 构建 `Settings`
- 提供默认配置

不负责：

- 调用 LLM
- 执行 Tool
- 控制 Runner

---

### `llm.py`

负责：

- 接收 `Settings`
- 使用配置里的模型、超时等参数

不负责：

- 决定配置从哪来

---

### `runner.py`

负责：

- 使用 `Settings.max_turns`
- 控制循环上限

不负责：

- 自己决定默认值写多少

---

## 7. 代码示例：第一版 Settings

下面给一个很适合你当前阶段的实现方式：

```python
import os


class Settings:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.openai_base_url = os.getenv("OPENAI_BASE_URL")
        self.model = os.getenv("MODEL", "gpt-5")
        self.max_turns = int(os.getenv("MAX_TURNS", "10"))
        self.request_timeout = int(os.getenv("REQUEST_TIMEOUT", "30"))
        self.max_retries = int(os.getenv("MAX_RETRIES", "2"))
        self.enable_tracing = os.getenv("ENABLE_TRACING", "true").lower() == "true"
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
```

这个版本有几个优点：

1. 足够简单
2. 不需要额外依赖
3. 已经能支撑你当前课程项目

这很适合作为 Sprint 阶段的第一版。

---

## 8. 为什么现在不急着上 Pydantic

很多人一看到配置管理，就马上想到：

```text
Pydantic Settings
Dynaconf
Hydra
```

这些都可以学，但不是现在第一优先级。

因为你当前的目标是：

> **先掌握 Agent 系统的主干。**

在这个阶段，一个清晰的原生 Python `Settings` 类已经足够。

等到后面进入部署、生产化、多环境切换时，再升级配置系统更合适。

这也是工程里很重要的一个原则：

> **先用最小设计解决当前问题。**

---

## 9. 本课代码改造点

如果你现在开始改自己的项目，建议按下面方式做：

### 第一步

在 `config.py` 里定义：

- `Settings`
- `load_settings()`

---

### 第二步

在 `app.py` 中统一创建：

```python
settings = Settings()
```

---

### 第三步

创建 LLM 时传入 `settings`：

```python
llm = OpenAILLM(settings)
```

---

### 第四步

Runner 也拿到同一个 `settings`：

```python
runner = Runner(settings=settings)
```

这样项目就开始形成一个很清晰的结构：

```text
app.py
  │
  ├── Settings
  ├── Agent
  ├── Runner
  └── OpenAILLM
```

而不是每个模块自己去“偷读”环境变量。

---

## 10. 这一课背后的设计思想

这一课表面上是在讲 Config。

但底层其实是在训练你一个更核心的工程能力：

> **把“变化点”从“稳定逻辑”里拆出来。**

为什么这很重要？

因为 Agent 项目里变化最快的通常不是 Loop 本身，而是：

- 模型
- 参数
- 环境
- 超时
- 重试策略
- 日志与 tracing 开关

如果这些变化点都压在业务逻辑里，系统会很快失控。

所以配置管理并不是“边角料”。

它是你从“会写 Demo”走向“会做工程”的关键一步。

---

## 11. 和官方框架对照理解

你后面看 OpenAI Agents SDK、LangGraph、AutoGen、OpenHands 这类项目时，会发现它们虽然 API 不同，但都有类似东西：

- model settings
- runtime options
- tracing settings
- retry policy
- session config

这说明一件事：

> **工程级 Agent 一定会把运行参数抽离出来。**

所以这一课不是“补充课”，而是主干课。

---

## 12. 本课小结

今天你要真正记住的不是某个类名，而是下面这句话：

> **配置不是细节，配置是运行系统的一部分。**

如果你把配置直接写死在逻辑里，那么项目只能停留在 Demo 阶段。

如果你开始把配置抽出来，你的项目才真正进入工程化阶段。

---

## 13. 本课作业

请你完成下面 4 个任务：

### 任务 1

在 `config.py` 中实现一个 `Settings` 类，至少包含：

- `openai_api_key`
- `model`
- `max_turns`
- `request_timeout`
- `max_retries`

---

### 任务 2

修改 `OpenAILLM`，不要再把模型名写死，改为从 `settings.model` 读取。

---

### 任务 3

修改 `Runner`，不要把循环次数写死，改为从 `settings.max_turns` 读取。

---

### 任务 4

思考并回答：

> 为什么“配置管理”本质上是在解决变化点管理问题？

---

## 14. 下一课预告

下一课我们继续推进工程化主线，进入：

> **Lesson5：Token 与上下文窗口管理初版**

到那时你会真正开始接触一个长任务 Agent 必须面对的问题：

```text
上下文不是无限的
```

你会理解为什么现代 Agent 框架一定要考虑：

- 历史截断
- 上下文压缩
- message 裁剪
- token 成本控制

这会是你从“能跑起来”走向“能长期运行”的重要一步。
