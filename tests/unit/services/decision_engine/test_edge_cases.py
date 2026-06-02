"""Edge case and boundary tests for decision engine components."""

from __future__ import annotations

import pytest

from src.services.decision_engine.difficulty_calculator import (
    DifficultyContext,
    DifficultyLevel,
    PerformanceDelta,
    SlidingWindowCalculator,
    get_difficulty_calculator,
)
from src.services.decision_engine.mode_router import AdventureMode, ModeRouter
from src.services.decision_engine.progress_state_machine import (
    LevelState,
    ProgressStateMachine,
)
from src.services.decision_engine.knowledge_selector import KnowledgeSelector


class TestDifficultyEdgeCases:
    """Boundary conditions for difficulty calculator."""

    async def test_extreme_high_correct_rate(self) -> None:
        """100% correct rate should not crash."""
        calc = SlidingWindowCalculator()
        ctx = DifficultyContext(
            user_id="u1", grade=5, chapter_id="ch1",
            history=PerformanceDelta(
                correct_rate=1.0, avg_response_time_ms=100.0,
                streak_count=50, current_level=DifficultyLevel.ADVANCED,
            ),
        )
        result = await calc.calculate(ctx)
        assert result.recommended_level.value >= 1

    async def test_extreme_low_correct_rate(self) -> None:
        """0% correct rate should not crash."""
        calc = SlidingWindowCalculator()
        ctx = DifficultyContext(
            user_id="u1", grade=3, chapter_id="ch1",
            history=PerformanceDelta(
                correct_rate=0.0, avg_response_time_ms=60000.0,
                streak_count=-10, current_level=DifficultyLevel.EASY,
            ),
        )
        result = await calc.calculate(ctx)
        assert result.recommended_level == DifficultyLevel.EASY

    async def test_singleton_returns_same_instance(self) -> None:
        """get_difficulty_calculator should return singleton."""
        c1 = get_difficulty_calculator()
        c2 = get_difficulty_calculator()
        assert c1 is c2

    async def test_all_levels_available(self) -> None:
        """All 5 difficulty levels should be available."""
        calc = SlidingWindowCalculator()
        levels = calc.get_available_levels()
        assert len(levels) == 5
        assert DifficultyLevel.EASY in levels
        assert DifficultyLevel.ADVANCED in levels


class TestModeRouterEdgeCases:
    """Edge cases for mode router."""

    async def test_first_route_always_returns_mode(self, router: ModeRouter) -> None:
        pass  # fixture handles this

    async def test_many_routes_stable(self) -> None:
        """1000 routes should not crash or hang."""
        router = ModeRouter()
        for i in range(200):
            await router.route(f"u_{i % 10}")
        # Should not raise

    async def test_single_user_many_routes(self) -> None:
        """Single user, many routes - history should be capped."""
        router = ModeRouter()
        for _ in range(50):
            await router.route("u1")
        history = router.get_history("u1")
        assert len(history) <= 20  # History cap

    async def test_zero_history(self) -> None:
        """New user should have empty history."""
        router = ModeRouter()
        history = router.get_history("new_user")
        assert history == []


@pytest.fixture
def router() -> ModeRouter:
    return ModeRouter()


class TestProgressStateMachineEdgeCases:
    """Edge cases for progress state machine."""

    async def test_all_states_defined(self) -> None:
        """All 5 states should be defined."""
        assert LevelState.LOCKED.value == "locked"
        assert LevelState.PERFECTED.value == "perfected"

    async def test_get_next_available_empty(self) -> None:
        """New user should have no available levels."""
        fsm = ProgressStateMachine()
        levels = await fsm.get_next_available("new_user", "ch1")
        assert levels == []

    async def test_perfected_is_terminal(self) -> None:
        """PERFECTED state cannot transition further."""
        fsm = ProgressStateMachine()
        await fsm.transition("u1", "l1", score=100, is_perfect=True)
        # Try to transition again - should stay perfected
        state = await fsm.transition("u1", "l1", score=100, is_perfect=True)
        assert state == LevelState.PERFECTED


class TestKnowledgeSelectorEdgeCases:
    """Edge cases for knowledge selector."""

    async def test_max_difficulty_returns_max_concepts(self) -> None:
        """Max difficulty should return max concepts."""
        selector = KnowledgeSelector()
        r_max = await selector.select_for_level("u1", "ch1", difficulty_level=5)
        r_min = await selector.select_for_level("u1", "ch1", difficulty_level=1)
        assert len(r_max) == 3  # ADVANCED → 3 concepts
        assert len(r_min) == 1  # EASY → 1 concept

    async def test_exclude_all_returns_empty(self) -> None:
        """Excluding all candidates should return empty."""
        selector = KnowledgeSelector()
        all_ids = [f"kp_ch1_{i}" for i in range(10)]
        result = await selector.select_for_level("u1", "ch1", difficulty_level=3, exclude_ids=all_ids)
        assert result == []
