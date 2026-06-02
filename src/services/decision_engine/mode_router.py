"""模式路由器 — 三种冒险模式轮换（英雄/导师/探索 = 3:1:1）。"""

from __future__ import annotations

from enum import StrEnum


class AdventureMode(StrEnum):
    """冒险模式 — 对齐 SRS REQ-MOD-001。"""
    HERO = "hero"         # 英雄模式：解决数学危机
    MENTOR = "mentor"     # 导师模式：教别人学数学
    EXPLORE = "explore"   # 探索模式：自由发现数学彩蛋


# 模式轮换权重（SRS REQ-MOD-001 Scenario 1）
MODE_WEIGHTS: dict[AdventureMode, int] = {
    AdventureMode.HERO: 3,
    AdventureMode.MENTOR: 1,
    AdventureMode.EXPLORE: 1,
}

# 不允许连续同一模式的次数上限
MAX_CONSECUTIVE_SAME_MODE: int = 3


class ModeRouter:
    """冒险模式路由器。

    基于 REQ-MOD-001 的 3:1:1 轮换策略，
    跟踪用户历史模式序列，确保不连续 3 关使用同一模式。
    """

    def __init__(self) -> None:
        self._history: dict[str, list[AdventureMode]] = {}

    async def route(
        self,
        user_id: str,
    ) -> AdventureMode:
        """路由到最合适的冒险模式。

        策略：3:1:1 加权随机，但最近 2 关的模式权重减半，
        确保不连续 3 次同一模式。

        Args:
            user_id: 学生用户 ID

        Returns:
            推荐的冒险模式
        """
        import random

        history = self._history.get(user_id, [])
        weights = dict(MODE_WEIGHTS)

        # 最近 2 关的模式降权
        for mode in history[-2:]:
            weights[mode] = max(0, weights[mode] - 1)

        # 如果已连续 2 次相同模式 → 强制排除
        if len(history) >= MAX_CONSECUTIVE_SAME_MODE - 1:
            recent_set = set(history[-(MAX_CONSECUTIVE_SAME_MODE - 1):])
            if len(recent_set) == 1:
                weights[list(recent_set)[0]] = 0

        # 加权随机选择
        modes = list(weights.keys())
        w = [weights[m] for m in modes]
        chosen = random.choices(modes, weights=w, k=1)[0]

        # 记录历史
        history.append(chosen)
        if len(history) > 20:
            history = history[-20:]
        self._history[user_id] = history

        return chosen

    def get_history(self, user_id: str) -> list[AdventureMode]:
        """获取用户模式历史。"""
        return self._history.get(user_id, [])
