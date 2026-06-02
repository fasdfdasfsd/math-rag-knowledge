"""难度计算器 — 滑动窗口算法（v2.0），v2.1 升级 IRT/BKT。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Final

# 难度计算权重（SRS REQ-ADP-001）
WEIGHT_MASTERY: Final[float] = 0.4
WEIGHT_FORGETTING: Final[float] = 0.2
WEIGHT_EMOTION: Final[float] = 0.2
WEIGHT_PROGRESS: Final[float] = 0.2

# 甜蜜点区间
SWEET_SPOT_LOW: Final[float] = 0.5
SWEET_SPOT_HIGH: Final[float] = 0.7

# 连续错误后降难度阈值
CONSECUTIVE_ERROR_THRESHOLD: Final[int] = 2

# 艾宾浩斯遗忘曲线衰减系数（默认 7 天半衰期）
DEFAULT_FORGETTING_DECAY: Final[float] = 0.1


class DifficultyLevel(IntEnum):
    """难度等级，1-5 对应小学数学由易到难。"""
    EASY = 1
    MEDIUM = 2
    HARD = 3
    CHALLENGING = 4
    ADVANCED = 5


@dataclass(frozen=True)
class PerformanceDelta:
    """学生近期的表现变化量。"""
    correct_rate: float
    avg_response_time_ms: float
    streak_count: int
    current_level: DifficultyLevel
    knowledge_gaps: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class DifficultyResult:
    """难度计算输出。"""
    recommended_level: DifficultyLevel
    expected_correct_prob: float
    sub_skills: list[str] = field(default_factory=list)
    reason: str = ""


@dataclass(frozen=True)
class DifficultyContext:
    """难度计算所需上下文。"""
    user_id: str
    grade: int
    chapter_id: str
    history: PerformanceDelta


class DifficultyCalculator(ABC):
    """难度计算器抽象基类。"""

    @abstractmethod
    async def calculate(self, context: DifficultyContext) -> DifficultyResult:
        """根据上下文计算推荐难度。"""
        ...

    @abstractmethod
    async def adjust(
        self, current: DifficultyResult, performance: PerformanceDelta,
    ) -> DifficultyResult:
        """根据实时表现动态调整难度。"""
        ...

    @abstractmethod
    def get_available_levels(self) -> list[DifficultyLevel]:
        """返回当前实现支持的所有难度等级。"""
        ...


class SlidingWindowCalculator(DifficultyCalculator):
    """滑动窗口难度计算器（v2.0 MVP 实现）。

    算法：难度 = f(掌握度×0.4, 遗忘×0.2, 情绪×0.2, 进度×0.2)
    目标：P(正确) ∈ [0.5, 0.7] 甜蜜点
    """

    def __init__(self, forgetting_decay: float = DEFAULT_FORGETTING_DECAY) -> None:
        self._forgetting_decay = forgetting_decay

    async def calculate(self, context: DifficultyContext) -> DifficultyResult:
        """综合加权计算推荐难度。"""
        h = context.history

        # 1. 掌握度因子：正确率越高 → 难度越高
        mastery_factor = h.correct_rate

        # 2. 遗忘因子：连续正确越多 → 遗忘越少 → 可以加难度
        forgetting_factor = max(0.0, 1.0 - self._forgetting_decay * max(0, 7 - h.streak_count))

        # 3. 情绪因子：连续错误 → 降难度保护信心（Zearn 模式）
        if h.streak_count < -CONSECUTIVE_ERROR_THRESHOLD:
            emotion_factor = -0.15  # 惩罚性降难度
        else:
            emotion_factor = 0.0

        # 4. 进度因子：不超出年级范围
        grade_max_level = min(DifficultyLevel.ADVANCED, DifficultyLevel(context.grade // 2 + 1))
        progress_factor = 0.0  # 默认不限制

        # 综合计算
        raw_score = (
            WEIGHT_MASTERY * mastery_factor
            + WEIGHT_FORGETTING * forgetting_factor
            + WEIGHT_EMOTION * emotion_factor
            + WEIGHT_PROGRESS * progress_factor
        )

        # 映射到难度等级：raw_score 0.0→EASY, 1.0→ADVANCED
        level = self._score_to_level(raw_score, grade_max_level)
        expected_prob = 0.5 + 0.2 * (1.0 - raw_score)  # 难度越高，预期正确率越低

        return DifficultyResult(
            recommended_level=level,
            expected_correct_prob=round(expected_prob, 3),
            reason=(
                f"mastery={mastery_factor:.2f}, forgetting={forgetting_factor:.2f}, "
                f"emotion={emotion_factor:.2f} → raw={raw_score:.2f} → level={level.name}"
            ),
        )

    async def adjust(
        self, current: DifficultyResult, performance: PerformanceDelta,
    ) -> DifficultyResult:
        """实时调整：连续错误降难度，连续正确持平或微升。"""
        if performance.streak_count >= 3:
            # 连续正确 ≥3 次 → 尝试升难度
            new_level = min(DifficultyLevel.ADVANCED, DifficultyLevel(current.recommended_level + 1))
        elif performance.streak_count <= -CONSECUTIVE_ERROR_THRESHOLD:
            # 连续错误 ≥2 次 → 降难度，但不回退基础等级（Zearn 模式）
            new_level = max(DifficultyLevel.EASY, DifficultyLevel(max(1, current.recommended_level - 1)))
        else:
            new_level = current.recommended_level

        return DifficultyResult(
            recommended_level=new_level,
            expected_correct_prob=current.expected_correct_prob,
            reason=f"adjusted from {current.recommended_level.name} → {new_level.name} (streak={performance.streak_count})",
        )

    def get_available_levels(self) -> list[DifficultyLevel]:
        """返回全部 5 个难度等级。"""
        return list(DifficultyLevel)

    # ---- 内部方法 ----

    def _score_to_level(self, raw_score: float, max_level: DifficultyLevel) -> DifficultyLevel:
        """将 0.0~1.0 原始分映射为难度等级，不超出 max_level。"""
        if raw_score <= 0.2:
            level = DifficultyLevel.EASY
        elif raw_score <= 0.4:
            level = DifficultyLevel.MEDIUM
        elif raw_score <= 0.6:
            level = DifficultyLevel.HARD
        elif raw_score <= 0.8:
            level = DifficultyLevel.CHALLENGING
        else:
            level = DifficultyLevel.ADVANCED
        return DifficultyLevel(min(level.value, max_level.value))


# 懒加载单例
_calculator: SlidingWindowCalculator | None = None


def get_difficulty_calculator() -> SlidingWindowCalculator:
    """获取难度计算器单例。"""
    global _calculator
    if _calculator is None:
        _calculator = SlidingWindowCalculator()
    return _calculator
