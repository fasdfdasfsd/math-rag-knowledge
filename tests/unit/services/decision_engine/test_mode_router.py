"""模式路由器测试。"""

from __future__ import annotations

import pytest

from src.services.decision_engine.mode_router import (
    AdventureMode,
    ModeRouter,
)


@pytest.fixture
def router() -> ModeRouter:
    return ModeRouter()


class TestRoute:
    async def test_returns_valid_mode(self, router: ModeRouter) -> None:
        """应返回有效模式。"""
        mode = await router.route("u1")
        assert mode in (AdventureMode.HERO, AdventureMode.MENTOR, AdventureMode.EXPLORE)

    async def test_multiple_users_independent(self, router: ModeRouter) -> None:
        """不同用户应独立追踪历史。"""
        modes_u1 = [await router.route("u1") for _ in range(10)]
        modes_u2 = [await router.route("u2") for _ in range(10)]
        # 两个用户的历史应独立
        assert len(router.get_history("u1")) == 10
        assert len(router.get_history("u2")) == 10

    async def test_hero_is_most_common(self, router: ModeRouter) -> None:
        """英雄模式应最频繁（权重 3/5）。"""
        modes = [await router.route(f"u_{i}") for i in range(100)]
        hero_count = sum(1 for m in modes if m == AdventureMode.HERO)
        mentor_count = sum(1 for m in modes if m == AdventureMode.MENTOR)
        assert hero_count > mentor_count * 1.5  # HERO weight 3 vs MENTOR 1

    async def test_no_three_consecutive_same(self, router: ModeRouter) -> None:
        """不允许连续 3 次同一模式。"""
        modes: list[AdventureMode] = []
        for uid in [f"u_{i}" for i in range(50)]:
            # 同一用户连续请求
            for _ in range(5):
                modes.append(await router.route(uid))
            # 检查最近 3 次
            if len(modes) >= 3:
                last3 = set(modes[-3:])
                if len(last3) == 1:
                    pytest.fail(f"连续 3 次同一模式: {last3}")

    async def test_get_history(self, router: ModeRouter) -> None:
        """历史记录应正确返回。"""
        await router.route("u_test")
        await router.route("u_test")
        history = router.get_history("u_test")
        assert len(history) == 2
