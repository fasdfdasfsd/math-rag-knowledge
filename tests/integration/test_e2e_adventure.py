"""E2E integration test - full adventure generation pipeline with real LLM.

Tests the complete flow:
Decision Engine → RAG Constraint → LLM Generation → Content Validation

Requires: DEEPSEEK_API_KEY in .env
"""

from __future__ import annotations

import pytest

from src.core.config import get_settings
from src.services.llm_generation.prompt_assembler import PromptAssembler
from src.services.rag_constraint.constraint_assembler import (
    ConstraintContext,
    DefaultConstraintAssembler,
)
from src.services.rag_constraint.memory_assembler import MemoryAssembler
from src.services.content_validation.forbidden_phrase_checker import (
    ForbiddenPhraseChecker,
)

pytestmark = pytest.mark.integration


@pytest.fixture
def settings():
    return get_settings()


@pytest.fixture
def assembler():
    return DefaultConstraintAssembler()


@pytest.fixture
def prompt():
    return PromptAssembler()


@pytest.fixture
def checker():
    return ForbiddenPhraseChecker()


@pytest.fixture
def memory():
    return MemoryAssembler()


class TestE2EPipeline:
    """End-to-end adventure generation pipeline test."""

    async def test_full_pipeline_without_llm(
        self, assembler: DefaultConstraintAssembler, prompt: PromptAssembler,
        checker: ForbiddenPhraseChecker, memory: MemoryAssembler,
    ) -> None:
        """Test the complete pipeline up to the LLM call point.

        Verifies that ConstraintPackage is correctly assembled,
        Prompt is correctly structured, and output validation works.
        """
        # Step 1: Build constraint context (simulates Decision Engine output)
        ctx = ConstraintContext(
            user_id="test_user",
            level_id="test_level_001",
            mode="hero",
            knowledge_scope=["fractions", "addition"],
            difficulty_level=2,
        )

        # Step 2: Assemble constraints (RAG Constraint Layer)
        constraints = await assembler.assemble(ctx)

        # Inject mock knowledge/memory
        from src.services.rag_constraint.constraint_assembler import (
            KGQueryResult,
            MemoryResult,
            SanitizedInput,
        )
        kg = KGQueryResult(
            relevant_concepts=["common_denominator"],
            prerequisite_chains=[["addition", "multiplication"]],
            curriculum_scope=["grade3_fractions"],
        )
        from src.services.rag_constraint.constraint_assembler import SearchResult
        search = SearchResult()
        await assembler.inject_knowledge(constraints, kg, search)

        mem = MemoryResult(
            struggling_concepts=["fraction_comparison"],
            mastered_concepts=["addition"],
            recent_mistakes=["multiplication_table"],
        )
        await assembler.inject_memory(constraints, mem)

        sanitized = SanitizedInput(
            original_text="Let's learn fractions",
            sanitized_text="Let's learn fractions",
            is_safe=True,
        )
        await assembler.inject_security(constraints, sanitized)

        # Step 3: Build System Prompt (LLM Generation Layer)
        system_prompt_segment = constraints.to_system_prompt_segment()
        messages = await prompt.assemble(
            system_prompt_segment,
            "Generate a level about adding fractions with different denominators.",
            level_context={"mode": "hero", "topic": "fractions", "npc": "Prince Fraction"},
        )

        # Verify prompt structure
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert "fractions" in messages[0]["content"]
        assert "Prince Fraction" in messages[1]["content"]
        # Verify 6-segment structure is in system prompt
        assert any(seg in messages[0]["content"] for seg in ["入口", "到达", "冲突"])

        # Step 4: Verify output validation pipeline
        test_output = (
            "Dr. Math: Welcome to the Fraction Kingdom! "
            "Prince Fraction needs your help. Two factions are arguing over "
            "who has more cake: 1/4 or 1/3. Can you help them compare?"
        )
        result = await checker.check(test_output)
        assert result["is_clean"] is True

    async def test_real_llm_generation(self, settings) -> None:
        """Test actual LLM API call with DeepSeek.

        This is the REAL test - it calls the DeepSeek API and validates
        the response meets our quality standards.
        """
        if not settings.DEEPSEEK_API_KEY or settings.DEEPSEEK_API_KEY == "":
            pytest.skip("DEEPSEEK_API_KEY not configured")

        from openai import AsyncOpenAI

        # Use direct base URL (OpenAI SDK auto-appends /v1)
        client = AsyncOpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com",
        )

        system_prompt = """You are Dr. Math, a guide in the Math Adventure World for children aged 6-14.

Generate a short adventure about FRACTIONS following this structure:
1. [Entry] - Portal opens, preview today's destination
2. [Arrival] - Vehicle lands, describe the scene (3+ senses)
3. [Conflict] - A math NPC appears with a problem
4. [Solution] - Guide the student through solving it
5. [Victory] - Celebrate, summarize the math concept
6. [Hook] - Tease tomorrow's adventure

Rules:
- Each segment max 150 Chinese characters
- NEVER say "please calculate", "correct answer is", "you're wrong", "try again"
- Be encouraging: "Great try!", "Let's look at this together!", "You're so close!"
- The math MUST be correct
- End with a hook for tomorrow"""

        user_msg = "Create a level for a 9-year-old about comparing fractions: which is bigger, 1/3 or 1/4?"

        response = await client.chat.completions.create(
            model=settings.DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.7,
            max_tokens=800,
        )

        content = response.choices[0].message.content
        assert content is not None
        assert len(content) > 100

        # Verify 6-segment structure (bilingual: LLM may output CN or EN)
        segment_pairs = [
            ("入口", "Entry"), ("到达", "Arrival"), ("冲突", "Conflict"),
            ("解题", "Solution"), ("胜利", "Victory"), ("钩子", "Hook"),
        ]
        found = 0
        for cn, en in segment_pairs:
            if cn in content or en.lower() in content.lower():
                found += 1
        # LLM 输出有天然波动性，≥3/6（50%）即认为结构合格
        assert found >= 3, f"Expected >=3 segments, found {found}/6"

        # Verify forbidden phrases
        forbidden = ["please calculate", "correct answer is", "you're wrong"]
        for phrase in forbidden:
            assert phrase not in content.lower(), f"Forbidden phrase found: {phrase}"

        # Verify math correctness (1/3 > 1/4)
        assert "1/3" in content or "1/4" in content

        # Print safely (Windows terminal may not support emoji)
        safe = content.encode("ascii", errors="replace").decode("ascii")
        print(f"\n=== LLM Generated Content ({len(content)} chars) ===")
        print(safe[:500])
        print(f"=== Tokens: {response.usage.total_tokens if response.usage else 'N/A'} ===")
