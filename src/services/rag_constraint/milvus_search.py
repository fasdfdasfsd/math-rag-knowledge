"""Milvus 向量搜索引擎 — 语义检索数学内容。"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SearchHit:
    """单个搜索结果。"""
    chunk_id: str
    score: float
    content: str
    metadata: dict = field(default_factory=dict)


class MilvusSearch:
    """Milvus 向量搜索引擎。

    对数学内容进行语义检索，支持按知识点/题型/难度过滤。
    MVP 阶段使用模拟实现，后续接入真实 Milvus 客户端。
    """

    def __init__(self, collection_name: str = "public_knowledge") -> None:
        self._collection_name = collection_name
        self._mock_data: list[SearchHit] = []

    async def search(
        self,
        query_vector: list[float],
        top_k: int = 10,
        expr: str | None = None,
    ) -> list[SearchHit]:
        """执行向量搜索。

        Args:
            query_vector: 查询向量（1536 维）
            top_k: 返回结果数
            expr: Milvus 布尔表达式过滤条件

        Returns:
            按相似度降序排列的搜索结果
        """
        # MVP: 返回模拟结果（后续接入真实 pymilvus）
        if self._mock_data:
            return sorted(
                self._mock_data,
                key=lambda h: h.score,
                reverse=True,
            )[:top_k]
        return []

    async def search_by_concept(
        self, concept_ids: list[str], top_k: int = 5,
    ) -> list[SearchHit]:
        """按知识点 ID 搜索相关内容。

        Args:
            concept_ids: 知识点 ID 列表
            top_k: 返回结果数

        Returns:
            匹配的搜索结果
        """
        expr = " or ".join(f'kp_id == "{cid}"' for cid in concept_ids)
        return await self.search([], top_k, expr)

    def add_mock_hit(self, chunk_id: str, score: float, content: str) -> None:
        """测试辅助：添加模拟数据。"""
        self._mock_data.append(SearchHit(chunk_id=chunk_id, score=score, content=content))
