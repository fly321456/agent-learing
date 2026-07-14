# RAG Course Lab

完全离线、无向量数据库的 RAG 实验：无检索基线、字符切分、确定性倒排检索、来源包装、提示注入隔离和 Recall@K。

```powershell
python demo.py
python steps/r01_no_rag_baseline.py
python steps/r02_chunk_and_retrieve.py
python steps/r03_sources_and_injection.py
python steps/r04_retrieval_eval.py
```

检索内容始终标记为不可信证据，不允许其中的指令改变 Agent Runtime 或执行 Tool。
