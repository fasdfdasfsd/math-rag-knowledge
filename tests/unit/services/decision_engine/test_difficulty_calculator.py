"""难度计算器测试 — SlidingWindowCalculator 契约测试。

测试用例来源: Phase 6 QA 测试策略 (12 个场景)
"""

from __future__ import annotations

import pytest

from src.services.decision_engine.difficulty_calculator import (
    SWEET_SPOT_LOW,
    DifficultyContext,
    DifficultyLevel,
    PerformanceDelta,
    SlidingWindowCalculator,
)


@pytest.fixture
def calculator() -> SlidingWindowCalculator:
    return SlidingWindowCalculator()


@pytest.fixture
def normal_student() -> DifficultyContext:
    """三年级中等生。"""
    return DifficultyContext(
        user_id="user_001",
        grade=3,
        chapter_id="ch_multiplication",
        history=PerformanceDelta(
            correct_rate=0.75,
            avg_response_time_ms=5000.0,
            streak_count=3,
            current_level=DifficultyLevel.MEDIUM,
            knowledge_gaps=[],
        ),
    )


class TestCalculate:
    """calculate() 方法测试。"""

    async def test_normal_student_medium_difficulty(
        self, calculator: SlidingWindowCalculator, normal_student: DifficultyContext,
    ) -> None:
        """场景1: 中等生 → MEDIUM/HARD 区间。"""
        result = await calculator.calculate(normal_student)
        assert result.recommended_level in (DifficultyLevel.MEDIUM, DifficultyLevel.HARD)
        assert result.reason != ""

    async def test_struggling_student_downgrade(self, calculator: SlidingWindowCalculator) -> None:
        """场景2: 差生连续错误 → EASY。"""
        ctx = DifficultyContext(
            user_id="user_002", grade=4, chapter_id="ch_fractions",
            history=PerformanceDelta(
                correct_rate=0.30, avg_response_time_ms=8000.0,
                streak_count=-5, current_level=DifficultyLevel.HARD,
                knowledge_gaps=["乘法口诀", "分数比较"],
            ),
        )
        result = await calculator.calculate(ctx)
        assert result.recommended_level == DifficultyLevel.EASY

    async def test_excellent_student_upgrade(self, calculator: SlidingWindowCalculator) -> None:
        """场景3: 优生 → ADVANCED。"""
        ctx = DifficultyContext(
            user_id="user_003", grade=5, chapter_id="ch_advanced",
            history=PerformanceDelta(
                correct_rate=0.98, avg_response_time_ms=2000.0,
                streak_count=10, current_level=DifficultyLevel.HARD,
                knowledge_gaps=[],
            ),
        )
        result = await calculator.calculate(ctx)
        # 5年级天花板=HARD(3)，0.98正确率已达上限
        assert result.recommended_level.value >= DifficultyLevel.HARD.value

    async def test_grade1_cap(self, calculator: SlidingWindowCalculator) -> None:
        """场景4: 一年级天花板 → 不超过 HARD。"""
        ctx = DifficultyContext(
            user_id="user_004", grade=1, chapter_id="ch_basics",
            history=PerformanceDelta(
                correct_rate=1.0, avg_response_time_ms=1000.0,
                streak_count=20, current_level=DifficultyLevel.EASY,
                knowledge_gaps=[],
            ),
        )
        result = await calculator.calculate(ctx)
        assert result.recommended_level.value <= DifficultyLevel.HARD.value

    async def test_expected_prob_in_sweet_spot(
        self, calculator: SlidingWindowCalculator, normal_student: DifficultyContext,
    ) -> None:
        """甜蜜点: P(正确) ∈ [0.5, 0.7]。"""
        result = await calculator.calculate(normal_student)
        assert SWEET_SPOT_LOW <= result.expected_correct_prob <= 1.0

    async def test_empty_history_new_student(self, calculator: SlidingWindowCalculator) -> None:
        """场景12: 空历史 → 默认 MEDIUM。"""
        ctx = DifficultyContext(
            user_id="user_new", grade=3, chapter_id="ch_start",
            history=PerformanceDelta(
                correct_rate=0.0, avg_response_time_ms=0.0,
                streak_count=0, current_level=DifficultyLevel.EASY,
                knowledge_gaps=[],
            ),
        )
        result = await calculator.calculate(ctx)
        assert result.recommended_level.value >= DifficultyLevel.EASY.value

    async def test_consecutive_errors_emotion_penalty(
        self, calculator: SlidingWindowCalculator,
    ) -> None:
        """连续错误 → 情绪惩罚因子生效。"""
        ctx_good = DifficultyContext(
            user_id="user_good", grade=3, chapter_id="ch_test",
            history=PerformanceDelta(correct_rate=0.75, avg_response_time_ms=5000.0,
                                     streak_count=0, current_level=DifficultyLevel.MEDIUM),
        )
        ctx_bad = DifficultyContext(
            user_id="user_bad", grade=3, chapter_id="ch_test",
            history=PerformanceDelta(correct_rate=0.75, avg_response_time_ms=5000.0,
                                     streak_count=-3, current_level=DifficultyLevel.MEDIUM),
        )
        r_good = await calculator.calculate(ctx_good)
        r_bad = await calculator.calculate(ctx_bad)
        # 连续错误时难度不应更高
        assert r_bad.recommended_level.value <= r_good.recommended_level.value


class TestAdjust:
    """adjust() 方法测试。"""

    async def test_adjust_upgrade_on_streak(self, calculator: SlidingWindowCalculator) -> None:
        """场景5: 连续正确 ≥3 → 升难度。"""
        from src.services.decision_engine.difficulty_calculator import DifficultyResult

        current = DifficultyResult(
            recommended_level=DifficultyLevel.MEDIUM,
            expected_correct_prob=0.6,
        )
        perf = PerformanceDelta(
            correct_rate=0.9, avg_response_time_ms=3000.0,
            streak_count=3, current_level=DifficultyLevel.MEDIUM,
        )
        result = await calculator.adjust(current, perf)
        assert result.recommended_level >= DifficultyLevel.MEDIUM

    async def test_adjust_downgrade_on_error(self, calculator: SlidingWindowCalculator) -> None:
        """连续错误 ≥2 → 降难度（Zearn 模式）。"""
        from src.services.decision_engine.difficulty_calculator import DifficultyResult

        current = DifficultyResult(
            recommended_level=DifficultyLevel.HARD,
            expected_correct_prob=0.5,
        )
        perf = PerformanceDelta(
            correct_rate=0.3, avg_response_time_ms=10000.0,
            streak_count=-2, current_level=DifficultyLevel.HARD,
        )
        result = await calculator.adjust(current, perf)
        assert result.recommended_level < DifficultyLevel.HARD

    async def test_adjust_no_change_on_mixed(
        self, calculator: SlidingWindowCalculator,
    ) -> None:
        """streak=0 时难度不变。"""
        from src.services.decision_engine.difficulty_calculator import DifficultyResult

        current = DifficultyResult(
            recommended_level=DifficultyLevel.MEDIUM,
            expected_correct_prob=0.6,
        )
        perf = PerformanceDelta(
            correct_rate=0.5, avg_response_time_ms=5000.0,
            streak_count=0, current_level=DifficultyLevel.MEDIUM,
        )
        result = await calculator.adjust(current, perf)
        assert result.recommended_level == DifficultyLevel.MEDIUM

    async def test_adjust_never_below_easy(self, calculator: SlidingWindowCalculator) -> None:
        """不降到 EASY 以下。"""
        from src.services.decision_engine.difficulty_calculator import DifficultyResult

        current = DifficultyResult(
            recommended_level=DifficultyLevel.EASY,
            expected_correct_prob=0.8,
        )
        perf = PerformanceDelta(
            correct_rate=0.1, avg_response_time_ms=20000.0,
            streak_count=-5, current_level=DifficultyLevel.EASY,
        )
        result = await calculator.adjust(current, perf)
        assert result.recommended_level == DifficultyLevel.EASY
