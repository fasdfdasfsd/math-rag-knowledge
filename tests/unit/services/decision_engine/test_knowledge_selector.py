"""Knowledge selector tests."""

from __future__ import annotations

import pytest

from src.services.decision_engine.knowledge_selector import KnowledgeSelector


@pytest.fixture
def selector() -> KnowledgeSelector:
    return KnowledgeSelector()


class TestSelectForLevel:
    async def test_returns_candidates(self, selector: KnowledgeSelector) -> None:
        """Should return candidate IDs for a chapter."""
        result = await selector.select_for_level("u1", "ch1", difficulty_level=3)
        assert len(result) >= 1

    async def test_excludes_ids(self, selector: KnowledgeSelector) -> None:
        """Should exclude specified IDs."""
        result = await selector.select_for_level(
            "u1", "ch1", difficulty_level=1,
            exclude_ids=["kp_ch1_0", "kp_ch1_1", "kp_ch1_2"],
        )
        assert "kp_ch1_0" not in result

    async def test_higher_difficulty_more_concepts(self, selector: KnowledgeSelector) -> None:
        """Higher difficulty should return more concepts."""
        r_easy = await selector.select_for_level("u1", "ch1", difficulty_level=1)
        r_hard = await selector.select_for_level("u1", "ch1", difficulty_level=5)
        assert len(r_hard) >= len(r_easy)
