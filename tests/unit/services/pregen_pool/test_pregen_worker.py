"""Pregen worker tests."""

from __future__ import annotations

import pytest

from src.services.pregen_pool.level_pregen_worker import LevelPregenWorker


class TestPregenWorker:
    async def test_pool_capacity(self) -> None:
        w = LevelPregenWorker(pool_size=5, ttl_hours=1)
        assert w.pool_capacity_remaining() == 5
        await w.pregenerate_levels(["a", "b", "c"])
        assert w.pool_capacity_remaining() == 2
        assert w.pool_available() == 3

    async def test_priority_sorting(self) -> None:
        w = LevelPregenWorker(pool_size=10, ttl_hours=1)
        await w.pregenerate_levels(["low"], priority=0)
        await w.pregenerate_levels(["high"], priority=2)
        hot = await w.get_predicted_hot_levels(limit=10)
        assert hot[0] == "high"

    async def test_pool_size_limit(self) -> None:
        w = LevelPregenWorker(pool_size=3, ttl_hours=1)
        r = await w.pregenerate_levels(["a", "b", "c", "d", "e"])
        assert r["generated"] == 3
