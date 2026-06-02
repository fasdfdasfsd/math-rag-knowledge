"""课程一致性校验器测试。"""

from __future__ import annotations

import pytest

from src.services.content_validation.curriculum_validator import (
    CurriculumValidator,
)


@pytest.fixture
def validator() -> CurriculumValidator:
    return CurriculumValidator()


class TestValidate:
    async def test_grade3_content_passes(self, validator: CurriculumValidator) -> None:
        """三年级内容应通过。"""
        result = await validator.validate(
            "小明用分数知识解决了问题，计算了三角形的面积。", grade=3, chapter_id="ch1",
        )
        assert result["is_aligned"] is True

    async def test_advanced_term_detected(self, validator: CurriculumValidator) -> None:
        """超纲术语应被检测。"""
        result = await validator.validate(
            "我们用函数来解决这个问题。", grade=3, chapter_id="ch1",
        )
        assert result["is_aligned"] is False
        assert any(d["term"] == "函数" for d in result["deviations"])

    async def test_multiple_deviations(self, validator: CurriculumValidator) -> None:
        """多个超纲术语应全部检出。"""
        result = await validator.validate(
            "用代数和几何证明来推导微积分公式。", grade=3, chapter_id="ch1",
        )
        assert len(result["deviations"]) >= 2
