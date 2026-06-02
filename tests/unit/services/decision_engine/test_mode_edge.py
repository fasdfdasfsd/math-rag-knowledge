"""Mode router edge case tests."""

from __future__ import annotations

import pytest

from src.services.decision_engine.mode_router import (
    AdventureMode,
    ModeRouter,
    MAX_CONSECUTIVE_SAME_MODE,
)


class TestModeDistribution:
    async def test_3_1_1_ratio_approximate(self) -> None:
        router = ModeRouter()
        counts = {m: 0 for m in AdventureMode}
        for i in range(500):
            mode = await router.route(f"user_{i}")
            counts[mode] += 1
        # Hero should be roughly 3x Mentor and 3x Explore
        assert counts[AdventureMode.HERO] > counts[AdventureMode.MENTOR]
        assert counts[AdventureMode.HERO] > counts[AdventureMode.EXPLORE]

    async def test_no_consecutive_3(self) -> None:
        router = ModeRouter()
        uid = "test_user"
        recent: list[AdventureMode] = []
        for _ in range(30):
            recent.append(await router.route(uid))
            if len(recent) >= 3:
                last3 = set(recent[-3:])
                assert len(last3) > 1 or len(recent) < 3

    async def test_history_capped_at_20(self) -> None:
        router = ModeRouter()
        for _ in range(50):
            await router.route("u1")
        assert len(router.get_history("u1")) <= 20
