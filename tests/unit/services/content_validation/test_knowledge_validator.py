"""Knowledge validator tests."""

from __future__ import annotations

import pytest

from src.services.content_validation.knowledge_validator import KnowledgeValidator


@pytest.fixture
def validator() -> KnowledgeValidator:
    return KnowledgeValidator()


class TestValidate:
    async def test_correct_arithmetic_passes(self, validator: KnowledgeValidator) -> None:
        """Correct arithmetic should pass."""
        result = await validator.validate("1 + 2 = 3", [])
        assert result["is_valid"] is True

    async def test_wrong_arithmetic_detected(self, validator: KnowledgeValidator) -> None:
        """Wrong arithmetic should be detected."""
        result = await validator.validate("2 + 2 = 5", [])
        assert result["is_valid"] is False

    async def test_multiple_expressions(self, validator: KnowledgeValidator) -> None:
        """Multiple expressions - all checked."""
        result = await validator.validate("3 + 1 = 4, 6 - 2 = 4", [])
        assert result["is_valid"] is True

    async def test_forbidden_math_phrase(self, validator: KnowledgeValidator) -> None:
        """"显然" should be flagged."""
        result = await validator.validate("显然这个结论成立", [])
        assert result["is_valid"] is False

    async def test_confidence_reduces_with_errors(self, validator: KnowledgeValidator) -> None:
        """Confidence should reduce with more errors."""
        r1 = await validator.validate("1+1=2", [])
        r2 = await validator.validate("1+1=3, 2+2=5, 显然成立", [])
        assert r1["confidence"] > r2["confidence"]
