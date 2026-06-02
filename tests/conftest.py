"""测试全局配置 — fixtures 和 pytest 插件。"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _override_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """确保测试环境使用安全的默认值，不依赖真实 .env。"""
    monkeypatch.setenv("DEBUG", "false")
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PASSWORD", "test_secret")
    monkeypatch.setenv("REDIS_PASSWORD", "test_secret")
    # Note: DEEPSEEK_API_KEY intentionally NOT overridden — E2E tests need real key
    monkeypatch.setenv("JWT_PRIVATE_KEY", "test-private")
    monkeypatch.setenv("JWT_PUBLIC_KEY", "test-public")
