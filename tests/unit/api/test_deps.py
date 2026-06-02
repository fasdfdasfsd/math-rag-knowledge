"""Dependency injection tests."""

from __future__ import annotations


def test_require_role_returns_callable() -> None:
    from src.api.deps import require_role
    fn = require_role("admin")
    assert callable(fn)

def test_require_admin_is_callable() -> None:
    from src.api.deps import require_admin
    assert callable(require_admin)

def test_require_parent_is_callable() -> None:
    from src.api.deps import require_parent
    assert callable(require_parent)
