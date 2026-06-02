"""Level pregen worker tests."""

from __future__ import annotations

import pytest

from src.services.pregen_pool.level_pregen_worker import LevelPregenWorker


@pytest.fixture
def worker() -> LevelPregenWorker:
    return LevelPregenWorker(pool_size=10, ttl_hours=1)


class TestPregenerateLevels:
    async def test_generates_levels(self, worker: LevelPregenWorker) -> None:
        """Should generate levels into pool."""
        result = await worker.pregenerate_levels(["l1", "l2", "l3"])
        assert result["generated"] == 3
        assert result["failed"] == 0
        assert worker.pool_available() == 3

    async def test_respects_pool_size(self, worker: LevelPregenWorker) -> None:
        """Should cap at pool_size."""
        result = await worker.pregenerate_levels([f"l{i}" for i in range(20)])
        assert result["generated"] == 10  # pool_size=10
        assert worker.pool_capacity_remaining() == 0

    async def test_empty_list(self, worker: LevelPregenWorker) -> None:
        """Empty list should generate nothing."""
        result = await worker.pregenerate_levels([])
        assert result["generated"] == 0

    async def test_hot_levels_returned_by_priority(self, worker: LevelPregenWorker) -> None:
        """High priority levels should be returned first."""
        await worker.pregenerate_levels(["l1", "l2"], priority=2)
        await worker.pregenerate_levels(["l3"], priority=0)
        hot = await worker.get_predicted_hot_levels(limit=10)
        # High priority items should come first
        assert hot[0] in ("l1", "l2")
