"""Rate limiter tests."""

from __future__ import annotations

import pytest

from src.services.security.rate_limiter import (
    RATE_LIMITS,
    InMemoryRateLimiter,
    get_rate_limiter,
)


@pytest.fixture
def limiter() -> InMemoryRateLimiter:
    return InMemoryRateLimiter()


class TestRateLimiter:
    async def test_allows_within_limit(self, limiter: InMemoryRateLimiter) -> None:
        """Should allow requests within the rate limit."""
        for _ in range(5):
            result = await limiter.check("test_key", max_requests=10, window_seconds=60)
            assert result.allowed is True

    async def test_blocks_exceeding_limit(self, limiter: InMemoryRateLimiter) -> None:
        """Should block requests exceeding the rate limit."""
        for _ in range(3):
            result = await limiter.check("block_test", max_requests=3, window_seconds=60)
            assert result.allowed is True
        # 4th request should be blocked
        result = await limiter.check("block_test", max_requests=3, window_seconds=60)
        assert result.allowed is False

    async def test_different_keys_independent(self, limiter: InMemoryRateLimiter) -> None:
        """Different keys should have independent counters."""
        for _ in range(3):
            await limiter.check("key_a", max_requests=3)
        # key_a is exhausted, key_b should still allow
        result = await limiter.check("key_b", max_requests=3)
        assert result.allowed is True

    async def test_remaining_count(self, limiter: InMemoryRateLimiter) -> None:
        """Should report correct remaining count."""
        result = await limiter.check("count_test", max_requests=5)
        assert result.remaining == 4

    async def test_predefined_limits(self) -> None:
        """Predefined rate limits should be sensible."""
        assert RATE_LIMITS["login"] == (5, 60)
        assert RATE_LIMITS["llm_generation"] == (10, 60)
        assert RATE_LIMITS["data_deletion"] == (3, 86400)

    async def test_reset_at_blocked(self, limiter: InMemoryRateLimiter) -> None:
        """验证被限流时 reset_at 在未来。"""
        for _ in range(2):
            await limiter.check("reset_test", max_requests=2, window_seconds=60)
        result = await limiter.check("reset_test", max_requests=2, window_seconds=60)
        assert result.allowed is False
        assert result.reset_at > 0

    async def test_default_window(self, limiter: InMemoryRateLimiter) -> None:
        """验证使用默认 max_requests=60 时第61次被限流。"""
        for _ in range(60):
            r = await limiter.check("default_test")
            assert r.allowed is True
        # 第61次触发限流
        r = await limiter.check("default_test")
        assert r.allowed is False

    async def test_empty_key_start(self, limiter: InMemoryRateLimiter) -> None:
        """验证新 key 从零窗口开始。"""
        result = await limiter.check("new_key", max_requests=5)
        assert result.allowed is True
        assert result.remaining == 4


class TestGetRateLimiter:
    def test_returns_same_instance(self) -> None:
        """验证 get_rate_limiter 返回单例。"""
        a = get_rate_limiter()
        b = get_rate_limiter()
        assert a is b

    def test_returns_in_memory_limiter(self) -> None:
        limiter = get_rate_limiter()
        assert isinstance(limiter, InMemoryRateLimiter)
