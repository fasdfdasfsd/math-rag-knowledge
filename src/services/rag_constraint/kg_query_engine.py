"""知识图谱查询引擎 — 查询知识点前置依赖/关联关系/大纲范围。"""

from __future__ import annotations

# 内置小学数学知识图谱（MVP 种子数据，后续从 DB 加载）
_BUILTIN_PREREQUISITES: dict[str, list[str]] = {
    "乘法": ["加法"],
    "乘法口诀": ["乘法"],
    "多位数乘法": ["乘法口诀"],
    "除法": ["乘法口诀"],
    "分数初步": ["除法"],
    "分数加减": ["分数初步", "通分"],
    "分数乘除": ["分数加减"],
    "小数": ["分数初步"],
    "面积": ["乘法"],
    "体积": ["面积", "乘法"],
    "方程": ["四则运算"],
}

_BUILTIN_RELATED: dict[str, list[str]] = {
    "分数加减": ["小数", "通分"],
    "乘法口诀": ["加法"],
    "面积": ["周长", "乘法"],
    "体积": ["面积"],
}


class KGQueryEngine:
    """知识图谱查询引擎。

    从知识图谱（MVP 使用内置字典，后续从 PostgreSQL 加载）
    查询前置依赖、关联关系和大纲范围。
    """

    def __init__(self) -> None:
        self._prerequisites: dict[str, list[str]] = dict(_BUILTIN_PREREQUISITES)
        self._related: dict[str, list[str]] = dict(_BUILTIN_RELATED)

    async def query_prerequisites(self, concept_id: str) -> list[str]:
        """查询指定知识点的前置依赖链（递归展开）。

        Args:
            concept_id: 知识点 ID 或名称

        Returns:
            前置知识点列表（从基础到目标排序）
        """
        result: list[str] = []
        visited: set[str] = set()

        def _walk(cid: str) -> None:
            if cid in visited:
                return
            visited.add(cid)
            for pre in self._prerequisites.get(cid, []):
                _walk(pre)
                if pre not in result:
                    result.append(pre)

        _walk(concept_id)
        return result

    async def query_related(self, concept_ids: list[str]) -> list[str]:
        """查询与给定知识点集合相关的其他知识点。

        Args:
            concept_ids: 知识点 ID/名称列表

        Returns:
            关联知识点列表
        """
        result: set[str] = set()
        for cid in concept_ids:
            for related in self._related.get(cid, []):
                if related not in concept_ids:
                    result.add(related)
        return list(result)

    async def query_curriculum_scope(self, grade: int, chapter_id: str) -> list[str]:
        """查询教学大纲范围内的知识点。

        Args:
            grade: 年级 (1-6)
            chapter_id: 章节 ID

        Returns:
            该年级+章节范围内的所有知识点
        """
        grade_prereqs: dict[int, list[str]] = {
            1: ["加法"],
            2: ["乘法", "乘法口诀"],
            3: ["除法", "分数初步", "小数"],
            4: ["分数加减", "面积"],
            5: ["分数乘除", "体积", "方程"],
            6: ["比例", "百分数"],
        }
        return grade_prereqs.get(grade, [])
