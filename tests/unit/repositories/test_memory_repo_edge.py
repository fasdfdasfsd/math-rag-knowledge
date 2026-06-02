"""Memory repo edge cases."""

from __future__ import annotations

import pytest

from src.repositories.memory_repo import MemoryRepository


@pytest.fixture
def repo() -> MemoryRepository:
    return MemoryRepository()


class TestMemoryRepoEdge:
    async def test_multiple_updates(self, repo: MemoryRepository) -> None:
        await repo.update_memory("u1", "s1", {"mastered": ["add"], "struggling": ["mult"]})
        await repo.update_memory("u1", "s2", {"mastered": ["mult"], "struggling": []})
        mastered = await repo.get_mastered_concepts("u1")
        assert "mult" in mastered

    async def test_nonexistent_user(self, repo: MemoryRepository) -> None:
        mistakes = await repo.get_recent_mistakes("no_such_user")
        assert mistakes == []
