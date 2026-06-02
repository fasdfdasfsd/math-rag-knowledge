---
category: Token成本优化
priority: recommended
updated: 2026-05-30
---

# Embedding 优化

## 概述

Embedding 是 RAG 系统的核心组件，其效率直接影响检索质量和成本。本规范涵盖 embedding 的批量处理、缓存策略、维度选择、增量更新以及向量索引优化，帮助在精度、速度和成本之间取得平衡。

## 核心规则

### 🔴 必须遵守 (MUST)

1. **相同文本不重复计算 embedding**
   - 实现 embedding 缓存层，对已处理过的文本直接返回缓存结果
   - 缓存 key 使用文本的 hash 值（如 SHA256）

2. **批量处理请求**
   - 单次 API 调用至少合并 100 条文本
   - 最大 batch size 建议 500（超出可能导致超时或截断）

### 🟡 强烈建议 (SHOULD)

1. **维度选择权衡**
   - 768 维：适合大规模文档（存储效率高，查询快）
   - 1536 维：通用场景（OpenAI ada-002 标准维度）
   - 3072 维：高精度场景（需要更高的检索质量）
   - 选择原则：在满足精度需求的前提下选择最低维度

2. **增量更新策略**
   - 新增文档时只计算新增内容的 embedding
   - 修改文档时删除旧 embedding，计算新 embedding
   - 全量重建仅在索引结构变更时执行

3. **pgvector 索引选择**
   - IVFFlat：构建快，适合静态或低频更新数据集
   - HNSW：查询快，适合高频查询场景（延迟敏感）

### 🟢 可选建议 (MAY)

1. **Embedding 模型归一化**
   - 使用 cosine similarity 时确保 embedding 已归一化
   - 归一化的 embedding 可以使用 IP（内积）替代 cosine 计算

2. **异步 embedding 生成**
   - 使用后台任务批量生成 embedding
   - 避免在请求链路上同步等待 embedding 生成

## 正确示例

```python
import hashlib
import asyncio
from typing import List
from dataclasses import dataclass
from functools import lru_cache


@dataclass
class Document:
    id: str
    text: str
    metadata: dict
    embedding: list[float] | None = None


class EmbeddingCache:
    """Embedding 缓存层"""
    
    def __init__(self):
        self._cache: dict[str, list[float]] = {}
    
    @staticmethod
    def _make_key(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
    
    def get(self, text: str) -> list[float] | None:
        return self._cache.get(self._make_key(text))
    
    def set(self, text: str, embedding: list[float]):
        self._cache[self._make_key(text)] = embedding
    
    def batch_get(self, texts: List[str]) -> List[list[float] | None]:
        return [self.get(t) for t in texts]


class EmbeddingService:
    """Embedding 服务，支持批量处理和缓存"""
    
    def __init__(self, model: str = "text-embedding-ada-002", batch_size: int = 200):
        self.model = model
        self.batch_size = batch_size
        self.cache = EmbeddingCache()
    
    async def embed_documents(self, documents: List[Document]) -> List[Document]:
        """批量生成文档 embedding"""
        results: List[Document] = []
        batch: List[Document] = []
        
        for doc in documents:
            # 检查缓存
            cached = self.cache.get(doc.text)
            if cached is not None:
                doc.embedding = cached
                results.append(doc)
                continue
            
            batch.append(doc)
            
            # 达到 batch size 时处理
            if len(batch) >= self.batch_size:
                await self._process_batch(batch)
                results.extend(batch)
                batch = []
        
        # 处理剩余
        if batch:
            await self._process_batch(batch)
            results.extend(batch)
        
        return results
    
    async def _process_batch(self, batch: List[Document]):
        """处理一个 batch 的 embedding 生成"""
        texts = [doc.text for doc in batch]
        
        # 调用 embedding API（此处为模拟）
        embeddings = await self._call_embedding_api(texts)
        
        # 更新缓存和文档对象
        for doc, emb in zip(batch, embeddings):
            self.cache.set(doc.text, emb)
            doc.embedding = emb
        
        print(f"[Embedding] 处理 batch: {len(batch)} 条文档")
    
    async def _call_embedding_api(self, texts: List[str]) -> List[List[float]]:
        """模拟 embedding API 调用"""
        # 实际生产环境中替换为真正的 API 调用
        # 例如：openai.Embedding.create(model=self.model, input=texts)
        await asyncio.sleep(0.1)  # 模拟网络延迟
        return [[0.0] * 1536 for _ in texts]  # 模拟结果
    
    def incremental_update(self, 
                          existing_docs: List[Document],
                          new_docs: List[Document],
                          updated_docs: List[tuple[Document, Document]]) -> List[Document]:
        """增量更新策略"""
        result = existing_docs.copy()
        
        # 新增文档
        for doc in new_docs:
            if self.cache.get(doc.text) is None:
                print(f"[Incremental] 新增文档: {doc.id}")
            result.append(doc)
        
        # 更新文档
        for old_doc, new_doc in updated_docs:
            # 删除旧的 embedding
            old_key = hashlib.sha256(old_doc.text.encode()).hexdigest()
            self.cache._cache.pop(old_key, None)
            print(f"[Incremental] 更新文档: {old_doc.id} -> {new_doc.id}")
            result[result.index(old_doc)] = new_doc
        
        return result
```

## 错误示例

```python
# 错误 1：每条文档单独调用 API
def bad_no_batch():
    """每条文档单独请求 embedding API"""
    docs = ["doc1", "doc2", ..., "doc1000"]
    for doc in docs:
        # 1000 次 API 调用，每次只有 1 条
        # 远不如 2 次 batch 调用（每次 500 条）
        embedding = call_api(doc)


# 错误 2：没有缓存层
def bad_no_cache():
    """每次处理相同文本都重新计算"""
    def process_query(query: str):
        # 即使 query 与之前完全相同
        # 每次都重新生成 embedding
        return generate_embedding(query)
    
    # 用户重复提问：白白计算 3 次
    process_query("FastAPI 路由怎么定义")
    process_query("FastAPI 路由怎么定义")  # 重复计算
    process_query("FastAPI 路由怎么定义")  # 重复计算


# 错误 3：维度选择不当
def bad_dimension_choice():
    """高维 embedding 不加控制"""
    # 1000 万条文档
    # 3072 维：需要 ~115GB 存储
    # 768 维：只需要 ~29GB 存储
    # 检索速度差异可达 4 倍
    dimension = 3072  # 对简单分类任务来说过高
    # 应优先评估 768 维是否满足精度需求


# 错误 4：全量重建的代价
def bad_full_rebuild():
    """每次更新都全量重建"""
    class BadVectorStore:
        def add_document(self, doc):
            # 添加一条文档
            self._rebuild_all_index()  # O(n) 重建，不必要
```

## 工具链配置

```python
# pgvector 索引选择示例
"""
-- IVFFlat 索引（适合大数据集，构建快）
CREATE INDEX ON documents USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- HNSW 索引（适合查询密集型，延迟敏感）
CREATE INDEX ON documents USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 200);

-- 查询时调整 probes
SET ivfflat.probes = 10;  -- IVFFlat probes 参数
SET hnsw.ef_search = 50;  -- HNSW ef_search 参数
"""
```

## 进阶专题

### RAG 系统中的 Embedding 缓存层次

```
Layer 1: 内存 LRU 缓存 (最近 1000 条)
Layer 2: Redis 持久化缓存 (TTL 7 天)
Layer 3: PostgreSQL 永久存储 (向量 + 元数据)
```

### 缓存 TTL 建议

| 数据类型 | TTL | 原因 |
|------|:--:|------|
| 用户查询 embedding | 1 小时 | 相同问题短时间重复 |
| 文档 chunk embedding | 永久 | 文档内容不变则向量不变 |
| 会话级临时向量 | 会话结束 | 一次性检索场景 |

### 维度选择决策矩阵

| 场景 | 推荐维度 | 存储 (1000万条) | 查询速度 |
|------|:--:|:--:|:--:|
| 大规模文档检索 | 768 | ~29GB | 4×(基准) |
| 通用 RAG | 1536 | ~58GB | 1×(基准) |
| 高精度语义搜索 | 3072 | ~115GB | 0.25× |

> 原则：在满足精度需求的前提下选择最低维度。

### 批量处理最佳实践

- 最小 batch：100 条
- 最优 batch：200-500 条
- 超大 batch 风险：超时、截断
- 异步后台处理，不在请求链路同步等待

### 参考来源

- [OpenAI Embedding API 文档](https://platform.openai.com/docs/guides/embeddings)
- [pgvector 官方文档](https://github.com/pgvector/pgvector)
