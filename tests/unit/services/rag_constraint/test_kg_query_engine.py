"""知识图谱查询引擎测试。"""

from __future__ import annotations

import pytest

from src.services.rag_constraint.kg_query_engine import KGQueryEngine


@pytest.fixture
def engine() -> KGQueryEngine:
    return KGQueryEngine()


class TestQueryPrerequisites:
    async def test_simple_chain(self, engine: KGQueryEngine) -> None:
        """多位数乘法 → 乘法口诀 → 乘法 → 加法。"""
        result = await engine.query_prerequisites("多位数乘法")
        assert "加法" in result
        assert "乘法" in result
        assert "乘法口诀" in result
        assert result.index("加法") < result.index("乘法") < result.index("乘法口诀")

    async def test_no_prerequisites(self, engine: KGQueryEngine) -> None:
        """加法没有前置依赖。"""
        result = await engine.query_prerequisites("加法")
        assert result == []

    async def test_unknown_concept(self, engine: KGQueryEngine) -> None:
        """未知知识点返回空列表。"""
        result = await engine.query_prerequisites("量子力学")
        assert result == []


class TestQueryRelated:
    async def test_finds_related(self, engine: KGQueryEngine) -> None:
        result = await engine.query_related(["分数加减"])
        assert "小数" in result or "通分" in result


class TestCurriculumScope:
    async def test_grade1_scope(self, engine: KGQueryEngine) -> None:
        result = await engine.query_curriculum_scope(grade=1, chapter_id="ch1")
        assert "加法" in result

    async def test_grade5_scope(self, engine: KGQueryEngine) -> None:
        result = await engine.query_curriculum_scope(grade=5, chapter_id="ch5")
        assert "方程" in result
