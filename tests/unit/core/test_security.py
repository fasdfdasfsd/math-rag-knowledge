"""Security module tests."""

from __future__ import annotations

import pytest

from src.core.security import hash_password, verify_password, verify_resource_ownership
from src.core.exceptions import ForbiddenException


class TestPasswordHashing:
    def test_hash_and_verify(self) -> None:
        hashed = hash_password("test123")
        assert verify_password("test123", hashed)

    def test_wrong_password_fails(self) -> None:
        hashed = hash_password("ok")
        assert not verify_password("nope", hashed)


class TestBOLA:
    def test_own_resource_passes(self) -> None:
        verify_resource_ownership("user_123", "user_123")

    def test_other_resource_raises(self) -> None:
        with pytest.raises(ForbiddenException):
            verify_resource_ownership("user_456", "user_789")
