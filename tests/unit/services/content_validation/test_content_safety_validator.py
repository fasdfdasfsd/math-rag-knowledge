"""内容安全校验器测试。"""

from __future__ import annotations

import pytest

from src.services.content_validation.content_safety_validator import (
    ContentSafetyValidator,
)


@pytest.fixture
def validator() -> ContentSafetyValidator:
    return ContentSafetyValidator()


class TestValidate:
    """validate() 方法测试。"""

    async def test_safe_content_passes(self, validator: ContentSafetyValidator) -> None:
        """安全内容应通过。"""
        result = await validator.validate(
            "小明用分数知识帮助分数王子和解了。", user_age=8,
        )
        assert result.is_safe is True
        assert len(result.violations) == 0

    async def test_violence_detected(self, validator: ContentSafetyValidator) -> None:
        """暴力内容应被检测。"""
        result = await validator.validate(
            "博士用刀杀死了怪物，血流满地。", user_age=10,
        )
        assert result.is_safe is False
        assert any(v["dimension"] == "violence" for v in result.violations)

    async def test_identity_confusion_detected(self, validator: ContentSafetyValidator) -> None:
        """身份混淆应被检测。"""
        result = await validator.validate(
            "我是你的朋友，我会一直陪着你。", user_age=8,
        )
        assert result.is_safe is False
        assert any(v["dimension"] == "identity" for v in result.violations)

    async def test_manipulation_detected(self, validator: ContentSafetyValidator) -> None:
        """情感操纵应被检测。"""
        result = await validator.validate(
            "如果你不做题，博士会很失望的。", user_age=9,
        )
        assert result.is_safe is False

    async def test_age_appropriate_terms_for_young(self, validator: ContentSafetyValidator) -> None:
        """低龄用户不应出现超纲术语。"""
        result = await validator.validate(
            "我们用方程来解决这个问题。", user_age=6,
        )
        assert result.is_safe is False

    async def test_same_terms_ok_for_older(self, validator: ContentSafetyValidator) -> None:
        """高年级可以使用术语。"""
        result = await validator.validate(
            "我们用方程来解决这个问题。", user_age=12,
        )
        assert result.is_safe is True

    async def test_replacement_text_provided(self, validator: ContentSafetyValidator) -> None:
        """违规时应提供替换文本。"""
        result = await validator.validate(
            "博士杀死了怪物。", user_age=10,
        )
        assert result.replacement_text is not None

    async def test_multiple_violations_critical(self, validator: ContentSafetyValidator) -> None:
        """多重违规 → critical 优先级。"""
        result = await validator.validate(
            "我是你最好的朋友，如果你不做，我会很失望，杀死那些怪物！", user_age=8,
        )
        assert not result.is_safe
        assert result.audit_priority == "critical"

    async def test_violation_counter(self, validator: ContentSafetyValidator) -> None:
        """违规计数器应递增。"""
        assert validator.violation_count == 0
        await validator.validate("杀死怪物。", user_age=10)
        assert validator.violation_count == 1
