"""Memory repository tests."""

from __future__ import annotations

import pytest

from src.repositories.memory_repo import MemoryRepository


@pytest.fixture
def repo() -> MemoryRepository:
    return MemoryRepository()


class TestMemoryRepo:
    async def test_get_recent_mistakes_empty(self, repo: MemoryRepository) -> None:
        """New user has no mistakes."""
        mistakes = await repo.get_recent_mistakes("u1")
        assert mistakes == []

    async def test_get_mastered_empty(self, repo: MemoryRepository) -> None:
        """New user has no mastered concepts."""
        mastered = await repo.get_mastered_concepts("u1")
        assert mastered == []

    async def test_get_struggling_empty(self, repo: MemoryRepository) -> None:
        """New user has no struggling concepts."""
        struggling = await repo.get_struggling_concepts("u1")
        assert struggling == []

    async def test_update_and_retrieve(self, repo: MemoryRepository) -> None:
        """Update memory then retrieve."""
        await repo.update_memory("u1", "s1", {
            "mistakes": [{"kp": "add", "answer": "wrong"}],
            "mastered": ["subtract"],
            "struggling": ["multiply"],
        })
        mistakes = await repo.get_recent_mistakes("u1", limit=5)
        assert len(mistakes) >= 1
        mastered = await repo.get_mastered_concepts("u1")
        assert "subtract" in mastered

    async def test_last_summary_none_by_default(self, repo: MemoryRepository) -> None:
        """Summary should be None for new users."""
        summary = await repo.get_last_session_summary("u1")
        assert summary is None
