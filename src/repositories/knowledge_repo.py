"""知识点/知识图谱数据访问层。"""

from __future__ import annotations


class KnowledgeRepository:
    """知识点与知识图谱数据操作（MVP 内存存储）。"""

    def __init__(self) -> None:
        self._concepts: dict[str, dict] = {}
        self._relations: list[dict] = []

    async def get_concept_by_id(self, concept_id: str) -> dict | None:
        return self._concepts.get(concept_id)

    async def get_prerequisites(self, concept_id: str) -> list[str]:
        return [r["source"] for r in self._relations if r["target"] == concept_id]

    async def list_concepts(self, grade: int | None = None) -> list[dict]:
        """List concepts, optionally filtered by grade."""
        if grade is not None:
            return [c for c in self._concepts.values() if c.get("grade") == grade]
        return list(self._concepts.values())

    async def get_curriculum_scope(self, grade: int, chapter_id: str) -> list[str]:
        return [cid for cid, c in self._concepts.items() if c.get("grade") == grade]

    async def upsert_concept(self, data: dict) -> dict:
        """Insert or update a concept."""
        cid = data["id"]
        self._concepts[cid] = data
        return data

    async def get_related_concepts(self, concept_ids: list[str]) -> list[str]:
        result: set[str] = set()
        for r in self._relations:
            if r["source"] in concept_ids:
                result.add(r["target"])
            if r["target"] in concept_ids:
                result.add(r["source"])
        return list(result - set(concept_ids))
