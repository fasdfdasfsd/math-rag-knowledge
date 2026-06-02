"""Integration test: Decision Engine → RAG → LLM → Validation pipeline."""

from __future__ import annotations

import pytest

from src.services.decision_engine.difficulty_calculator import (
    DifficultyContext,
    DifficultyLevel,
    PerformanceDelta,
    get_difficulty_calculator,
)
from src.services.decision_engine.mode_router import AdventureMode, ModeRouter
from src.services.decision_engine.knowledge_selector import KnowledgeSelector
from src.services.rag_constraint.constraint_assembler import (
    ConstraintContext,
    DefaultConstraintAssembler,
)
from src.services.llm_generation.prompt_assembler import PromptAssembler
from src.services.content_validation.forbidden_phrase_checker import (
    ForbiddenPhraseChecker,
)
from src.services.content_validation.content_safety_validator import (
    ContentSafetyValidator,
)


class TestDecisionPipeline:
    """Test Decision Engine + RAG Constraint integration."""

    async def test_difficulty_to_constraint_flow(self) -> None:
        """Decision Engine output should feed into RAG Constraint."""
        calc = get_difficulty_calculator()
        ctx = DifficultyContext(
            user_id="u1", grade=3, chapter_id="ch_fractions",
            history=PerformanceDelta(
                correct_rate=0.7, avg_response_time_ms=5000.0,
                streak_count=2, current_level=DifficultyLevel.MEDIUM,
            ),
        )
        result = await calc.calculate(ctx)

        # Feed difficulty into constraint context
        constraint_ctx = ConstraintContext(
            user_id="u1", level_id="l1", mode="hero",
            knowledge_scope=["fractions"], difficulty_level=result.recommended_level.value,
        )
        assert constraint_ctx.difficulty_level >= DifficultyLevel.EASY.value

    async def test_mode_and_knowledge_integration(self) -> None:
        """Mode router + knowledge selector work together."""
        router = ModeRouter()
        selector = KnowledgeSelector()

        mode = await router.route("u1")
        assert mode in (AdventureMode.HERO, AdventureMode.MENTOR, AdventureMode.EXPLORE)

        kps = await selector.select_for_level("u1", "ch1", difficulty_level=3)
        assert len(kps) >= 1

    async def test_full_validation_chain(self) -> None:
        """Forbidden phrase + content safety + curriculum validation."""
        checker = ForbiddenPhraseChecker()
        safety = ContentSafetyValidator()

        good_text = "真棒！我们一起来看看这个分数问题。"
        bad_text = "正确答案是5。杀死那个怪物。"

        # Good text passes both
        clean = await checker.check(good_text)
        assert clean["is_clean"]

        safe = await safety.validate(good_text, user_age=9)
        assert safe.is_safe

        # Bad text fails both
        dirty = await checker.check(bad_text)
        assert not dirty["is_clean"]

        unsafe = await safety.validate(bad_text, user_age=9)
        assert not unsafe.is_safe

    async def test_constraint_to_prompt_flow(self) -> None:
        """Constraint output should produce valid LLM prompt."""
        assembler = DefaultConstraintAssembler()
        prompt = PromptAssembler()

        constraints = await assembler.assemble(ConstraintContext(
            user_id="u1", level_id="l1", mode="hero",
            knowledge_scope=["fractions"], difficulty_level=2,
        ))
        system_segment = constraints.to_system_prompt_segment()
        messages = await prompt.assemble(system_segment, "Start adventure!")

        assert len(messages) == 2
        assert "fractions" in messages[0]["content"]
        assert messages[1]["content"] == "Start adventure!"
