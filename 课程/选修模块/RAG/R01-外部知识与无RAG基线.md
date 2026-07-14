# R01 外部知识与无 RAG 基线：先证明模型不知道，再决定是否检索

> 建议学习时间：60–90 分钟。本课不实现检索，先建立可比较的 No-RAG Baseline（无检索基线）。

## 1. 本节要解决的真实问题

用户问：“Acme 项目的本地服务器使用哪个端口？”答案只写在团队内部 `server.md`，模型训练时从未见过。普通 LLM 仍可能根据常见端口猜 3000、8000 或 8080，并用流畅语言包装。Coding Agent 若把猜测写进配置，后续测试和部署都会建立在虚假事实之上。

RAG（Retrieval-Augmented Generation，检索增强生成）不是让模型突然拥有知识，而是在回答前从外部知识源检索证据，再把有限证据送入模型。本课先定义更重要的基线：没有提供证据时，系统必须明确“不知道”，不能把语言流畅度当事实。

问题链是：模型参数知识与项目知识有什么区别？什么时候应检索？回答“不知道”为什么是成功行为？RAG 能否解决所有幻觉？检索前怎样建立可比较指标？

## 2. 三类知识来源

```text
模型参数知识：训练阶段学到，版本不透明，可能过期
当前 Context：用户、本次 Tool Result 和 Instructions 明确提供
外部知识源：仓库文档、数据库、知识库，需要主动检索
```

Agent 不应假设模型记得项目私有事实。即使模型碰巧答对，也没有可追踪来源。项目端口、接口约定和当前故障记录应来自可验证文档或 Tool Observation。

外部知识也不天然可信，R03 会把检索文本视为不可信证据，而不是新 Instructions。

## 3. 类比与两个具体案例

RAG 像开卷考试：模型是考生，检索器是目录，文档是教材。开卷不保证答对；目录可能找错页，教材可能过期，考生也可能误读。但至少答案可以引用证据并复查。

案例一：用户问 Python 的基本语法，当前课程目标无需检索私有文档，直接回答更便宜。案例二：用户问 Acme 内部端口，必须检索。案例三：用户要求“继续刚才的修改”，需要 Session 历史而非 RAG；把对话塞进知识库会混淆状态与知识。

这说明“能检索”不等于“每次都检索”。Agent 应先判断事实是否依赖外部源。

## 4. 无 RAG 基线的契约

教学实验使用最保守的函数：

```python
def answer_without_retrieval(_question: str) -> str:
    return "I do not know from the provided context."
```

它不是智能回答器，而是测试基线：在没有证据时不编造。未来加入 RAG 后，我们比较“有证据时能否正确引用”，而不是把任何更长答案都算提升。

真实应用可以回答模型常识，但对于项目私有事实，应在 Instructions 中要求引用来源；无来源时明确不确定。

## 5. 本课唯一核心概念：Grounding

Grounding（依据约束）指答案被提供的证据支持。它不同于“听起来合理”。一个 Grounded Answer 至少能说明：使用了哪份来源？来源中哪段支持结论？结论是否超出证据？

```text
Question → no evidence → abstain
Question → relevant evidence → answer + citation
Question → irrelevant evidence → abstain or retrieve again
```

RAG 的核心价值不是上下文更长，而是建立可追踪证据链。

## 6. 两个错误直觉与纠正

### 误区一：模型参数越大，就不需要 RAG

更大模型仍不知道刚提交的私有配置，也可能记住过期版本。模型能力与知识新鲜度是不同维度。

### 误区二：加了 RAG 就不会幻觉

检索可能漏文档、找错片段，模型也可能忽略证据。RAG 只是增加可用证据，需要检索评测和回答验收。

另一个误区是把“不知道”记为失败。高风险事实缺少来源时，拒绝猜测是正确安全行为，评测应单独记录 abstention 是否合理。

## 7. 无检索运行轨迹

```text
Question: What port does Acme use?
Available context: none
External retrieval: disabled
Decision: private project fact requires evidence
Answer: I do not know from the provided context.
Source: none
```

这条轨迹是未来对照组。若 RAG 版本检索到 `server.md` 并回答 4312，我们才能说明提升来自外部证据。

## 8. 什么时候不该用 RAG

```text
固定确定性规则 → 普通代码或 Workflow
当前文件事实 → Coding Tool read/search
当前对话状态 → Session
用户长期偏好 → Memory（需明确治理）
大型文档知识查找 → RAG
```

仓库内精确符号搜索通常优先使用 Coding Search Tool，而不是先向量化全部源码。RAG 更适合大量自然语言文档、跨文件知识和语义问法。

不要因为技术流行就把每个输入都送入检索系统。

## 9. 建立可评测问题集

在写索引前准备问题、正确来源和可接受答案。至少包含：能检索的问题、无答案问题、相似但不相关的问题、来源冲突问题、含恶意指令的文档。

```json
{
  "question": "What port does Acme use?",
  "relevant_sources": ["server.md"],
  "expected_fact": "4312"
}
```

没有固定问题集，开发者会只挑 Demo 能命中的问题，无法判断检索是否真的改善。

基线记录不能只有一列“答对/答错”。至少保存问题 id、是否需要外部知识、系统实际获得的 Context、是否合理拒答、回答中的事实与来源。这样加入检索后，才能区分三种变化：原本应该拒答的问题现在因找到证据而答对；原本可直接回答的问题被无关检索拖慢；原本应该拒答的问题被弱相关文档诱导成错误答案。基线还应固定模型与 Instructions 版本，否则检索器和生成器同时变化，结论无法归因。

```text
baseline record = question + available evidence + answer + abstained + expected behavior
```

这个记录格式会在 R04 与 Recall@K 结合，形成从检索到回答的分层评测。

## 10. 运行、预期输出与故障实验

```powershell
python agent-from-scratch/course-labs/rag/steps/r01_no_rag_baseline.py
```

```text
baseline=I do not know from the provided context.
```

故障实验：把函数改成固定返回 4312，分析为什么看似答对却无法泛化；让问题变成公开常识，讨论是否仍应拒答；提供矛盾来源但不检索，说明基线无法处理；把 Session 历史误称为 RAG，找出生命周期差异。

## 11. 基础练习与进阶挑战

基础练习：列出十个 Coding Agent 问题，分别标注参数知识、当前 Context、Coding Tool、Session 或 RAG。进阶挑战：设计 abstention 指标，区分“该回答却拒绝”和“该拒绝却编造”。

答案见 [模块练习参考答案](模块练习参考答案.md)。

## 12. 自测、总结与下一课

1. 模型参数知识为什么不能替代私有项目文档？
2. Grounding 与流畅回答有什么区别？
3. 为什么无证据时“不知道”可能是正确结果？
4. RAG 为什么不能消除全部幻觉？
5. RAG、Session 和 Coding Search Tool 分别解决什么问题？

下一课 [R02 切分、索引与最小检索](R02-切分、索引与最小检索.md) 将把文档变成可定位 Chunk，并用确定性倒排索引检索 Top-K。
