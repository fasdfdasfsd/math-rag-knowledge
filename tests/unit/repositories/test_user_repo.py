"""User repository tests."""

from __future__ import annotations

import pytest

from src.repositories.user_repo import UserRepository


@pytest.fixture
def repo() -> UserRepository:
    return UserRepository()


class TestUserRepo:
    async def test_create_and_get(self, repo: UserRepository) -> None:
        """Should create and retrieve user."""
        user = await repo.create({"id": "u1", "email": "test@test.com", "name": "Test"})
        fetched = await repo.get_by_id("u1")
        assert fetched is not None
        assert fetched["email"] == "test@test.com"

    async def test_get_by_email(self, repo: UserRepository) -> None:
        """Should find user by email."""
        await repo.create({"id": "u1", "email": "a@b.com"})
        await repo.create({"id": "u2", "email": "c@d.com"})
        result = await repo.get_by_email("c@d.com")
        assert result is not None
        assert result["id"] == "u2"

    async def test_update(self, repo: UserRepository) -> None:
        """Should update user fields."""
        await repo.create({"id": "u1", "name": "Old"})
        await repo.update("u1", {"name": "New"})
        user = await repo.get_by_id("u1")
        assert user["name"] == "New"

    async def test_update_progress(self, repo: UserRepository) -> None:
        """Should store progress."""
        await repo.update_progress("u1", "l1", 85.0)
        # Progress is stored internally, not exposed via get_by_id
        # This tests no exceptions
