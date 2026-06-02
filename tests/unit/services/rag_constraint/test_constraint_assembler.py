"""约束组装器测试。"""

from __future__ import annotations

import pytest

from src.services.rag_constraint.constraint_assembler import (
    AssembledConstraints,
    ConstraintContext,
    DefaultConstraintAssembler,
    KGQueryResult,
    MemoryResult,
    SanitizedInput,
    SearchResult,
)


@pytest.fixture
def assembler() -> DefaultConstraintAssembler:
    return DefaultConstraintAssembler()


class TestAssemble:
    """assemble() 方法测试。"""

    async def test_creates_constraints_with_knowledge_scope(
        self, assembler: DefaultConstraintAssembler,
    ) -> None:
        """基础字段应正确初始化。"""
        ctx = ConstraintContext(
            user_id="u1", level_id="l1", mode="hero",
            knowledge_scope=["分数", "通分"], difficulty_level=3,
        )
        result = await assembler.assemble(ctx)
        assert "分数" in result.knowledge_scope
        assert result.difficulty_level == 3


class TestInjectKnowledge:
    """inject_knowledge() 方法测试。"""

    async def test_adds_concepts_and_marks_missing_prereqs(
        self, assembler: DefaultConstraintAssembler,
    ) -> None:
        """前置依赖中未掌握的概念 → forbidden_topics。"""
        constraints = AssembledConstraints(knowledge_scope=["分数加法"])
        kg = KGQueryResult(
            relevant_concepts=["通分"],
            prerequisite_chains=[["分数基础", "乘法口诀"]],
            curriculum_scope=["三年级上"],
        )
        search = SearchResult()
        await assembler.inject_knowledge(constraints, kg, search)
        assert "通分" in constraints.knowledge_scope
        # 未掌握的前置依赖应被禁止
        assert any("分数基础" in t for t in constraints.forbidden_topics)
        assert any("乘法口诀" in t for t in constraints.forbidden_topics)


class TestInjectMemory:
    """inject_memory() 方法测试。"""

    async def test_struggling_concepts_become_required(
        self, assembler: DefaultConstraintAssembler,
    ) -> None:
        """薄弱概念应加入 required_concepts。"""
        constraints = AssembledConstraints()
        mem = MemoryResult(
            struggling_concepts=["分数比较"], mastered_concepts=["加法"],
            recent_mistakes=["分数乘法"],
        )
        await assembler.inject_memory(constraints, mem)
        assert "分数比较" in constraints.required_concepts
        # 已掌握的不应再考
        assert "加法" in constraints.forbidden_topics
        assert constraints.memory_context is not None


class TestInjectSecurity:
    """inject_security() 方法测试。"""

    async def test_blocked_terms_added_to_forbidden(
        self, assembler: DefaultConstraintAssembler,
    ) -> None:
        """被封禁的术语应加入 forbidden_topics。"""
        constraints = AssembledConstraints()
        sanitized = SanitizedInput(
            original_text="test", sanitized_text="test",
            blocked_terms=["bad_word"], is_safe=True,
        )
        await assembler.inject_security(constraints, sanitized)
        assert "bad_word" in constraints.forbidden_topics


class TestBuildSystemPrompt:
    """build_system_prompt() 方法测试。"""

    async def test_produces_valid_prompt(self, assembler: DefaultConstraintAssembler) -> None:
        """应生成有效的 System Prompt 字符串。"""
        constraints = AssembledConstraints(
            knowledge_scope=["分数"],
            difficulty_level=2,
            forbidden_topics=["禁止内容X"],
            security_rules=["安全规则1"],
        )
        prompt = await assembler.build_system_prompt(constraints)
        assert "分数" in prompt
        assert "禁止内容X" in prompt
        assert "产品治理红线" in prompt  # 治理规则应注入

    async def test_empty_constraints_minimal_prompt(
        self, assembler: DefaultConstraintAssembler,
    ) -> None:
        """空约束集应生成最小可用 Prompt。"""
        constraints = AssembledConstraints()
        prompt = await assembler.build_system_prompt(constraints)
        assert len(prompt) > 0
        assert "产品治理红线" in prompt
