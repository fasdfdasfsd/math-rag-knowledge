"""进度状态机测试。"""

from __future__ import annotations

import pytest

from src.services.decision_engine.progress_state_machine import (
    LevelState,
    ProgressStateMachine,
)


@pytest.fixture
def fsm() -> ProgressStateMachine:
    return ProgressStateMachine()


class TestTransition:
    async def test_available_to_completed(self, fsm: ProgressStateMachine) -> None:
        """通过关卡: AVAILABLE → COMPLETED。"""
        state = await fsm.transition("u1", "l1", score=80, is_perfect=False)
        assert state == LevelState.COMPLETED

    async def test_perfect_leads_to_perfected(self, fsm: ProgressStateMachine) -> None:
        """满分 → PERFECTED。"""
        state = await fsm.transition("u1", "l2", score=100, is_perfect=True)
        assert state == LevelState.PERFECTED

    async def test_low_score_stays(self, fsm: ProgressStateMachine) -> None:
        """不及格 → 保持原状态。"""
        state = await fsm.transition("u1", "l3", score=30, is_perfect=False)
        assert state == LevelState.AVAILABLE  # 默认初始态

    async def test_unlock_next(self, fsm: ProgressStateMachine) -> None:
        """解锁下一关。"""
        await fsm.transition("u1", "l1", score=80, is_perfect=False)
        fsm.unlock_next("u1", "l1", "l2")
        next_available = await fsm.get_next_available("u1", "ch1")
        assert "l2" in next_available
