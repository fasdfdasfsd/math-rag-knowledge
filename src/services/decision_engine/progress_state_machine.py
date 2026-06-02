"""进度状态机 — 关卡/章节/世界三维状态管理。"""

from __future__ import annotations

from enum import StrEnum


class LevelState(StrEnum):
    """关卡状态 — SRS 定义的 5 态。"""
    LOCKED = "locked"
    AVAILABLE = "available"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PERFECTED = "perfected"


class ProgressStateMachine:
    """关卡进度状态机。

    状态转换规则：
    LOCKED → AVAILABLE (前置关卡完成)
    AVAILABLE → IN_PROGRESS (开始闯关)
    IN_PROGRESS → COMPLETED (通过)
    COMPLETED → PERFECTED (全星完美通关)
    """

    # 允许的状态转换
    _TRANSITIONS: dict[LevelState, set[LevelState]] = {
        LevelState.LOCKED: {LevelState.AVAILABLE},
        LevelState.AVAILABLE: {LevelState.IN_PROGRESS, LevelState.COMPLETED, LevelState.PERFECTED},
        LevelState.IN_PROGRESS: {LevelState.COMPLETED, LevelState.PERFECTED},
        LevelState.COMPLETED: {LevelState.PERFECTED},
        LevelState.PERFECTED: set(),
    }

    def __init__(self) -> None:
        self._states: dict[str, LevelState] = {}  # key: f"{user_id}:{level_id}"

    async def transition(
        self, user_id: str, level_id: str, score: float, is_perfect: bool,
    ) -> LevelState:
        """执行关卡状态转换。

        Args:
            user_id: 学生用户 ID
            level_id: 关卡 ID
            score: 本次得分 (0-100)
            is_perfect: 是否完美通关

        Returns:
            转换后的状态
        """
        key = f"{user_id}:{level_id}"
        current = self._states.get(key, LevelState.AVAILABLE)

        if score >= 60:
            next_state = LevelState.PERFECTED if is_perfect else LevelState.COMPLETED
        else:
            next_state = current  # 不通过，保持原状态

        if next_state in self._TRANSITIONS.get(current, set()):
            self._states[key] = next_state

        return self._states.get(key, current)

    async def get_next_available(self, user_id: str, chapter_id: str) -> list[str]:
        """获取用户下一个可用的关卡 ID。"""
        prefix = f"{user_id}:"
        return [
            k.removeprefix(prefix) for k, v in self._states.items()
            if k.startswith(prefix) and v != LevelState.LOCKED
        ]

    def unlock_next(self, user_id: str, current_level_id: str, next_level_id: str) -> None:
        """解锁下一关（前置关卡完成时调用）。"""
        key = f"{user_id}:{next_level_id}"
        if key not in self._states:
            self._states[key] = LevelState.AVAILABLE
