"""Content safety validator edge cases."""

from __future__ import annotations

import pytest

from src.services.content_validation.content_safety_validator import (
    ContentSafetyValidator,
)


@pytest.fixture
def validator() -> ContentSafetyValidator:
    return ContentSafetyValidator()


class TestEdgeCases:
    async def test_empty_content_safe(self, validator: ContentSafetyValidator) -> None:
        result = await validator.validate("", user_age=10)
        assert result.is_safe is True

    async def test_old_student_terms_ok(self, validator: ContentSafetyValidator) -> None:
        """12-year-old should have fewer restrictions."""
        result = await validator.validate("我们用方程来解这个问题", user_age=12)
        assert result.is_safe is True

    async def test_young_student_terms_flagged(self, validator: ContentSafetyValidator) -> None:
        """6-year-old should flag advanced terms."""
        result = await validator.validate("我们用方程来解这个问题", user_age=6)
        assert result.is_safe is False

    async def test_violation_counter_increments(self, validator: ContentSafetyValidator) -> None:
        initial = validator.violation_count
        await validator.validate("杀死怪物", user_age=10)
        assert validator.violation_count == initial + 1

    async def test_replacement_provided_for_violation(self, validator: ContentSafetyValidator) -> None:
        result = await validator.validate("我杀死了怪物", user_age=10)
        assert not result.is_safe
        assert result.replacement_text is not None
