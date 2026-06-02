"""速率限制器 — 基于 Redis 滑动窗口的请求限流。

实现 SRS REQ-NFR-S01（速率限制）+ 安全审计 V-03 修复。
"""

from __future__ import annotations

import time


class RateLimitResult:
    """限流检查结果。"""
    allowed: bool
    remaining: int
    reset_at: float

    def __init__(self, allowed: bool, remaining: int, reset_at: float) -> None:
        self.allowed = allowed
        self.remaining = remaining
        self.reset_at = reset_at


class InMemoryRateLimiter:
    """内存级速率限制器（MVP 无 Redis 时使用）。

    基于滑动窗口计数器，单进程适用。
    """

    def __init__(self) -> None:
        self._windows: dict[str, list[float]] = {}

    async def check(
        self,
        key: str,
        max_requests: int = 60,
        window_seconds: int = 60,
    ) -> RateLimitResult:
        """检查是否超过速率限制。

        Args:
            key: 限流 key（如 "user:{id}:llm", "ip:{addr}:login"）
            max_requests: 窗口内最大请求数
            window_seconds: 窗口大小（秒）

        Returns:
            限流结果
        """
        now = time.monotonic()
        cutoff = now - window_seconds

        # 滑动窗口：移除过期记录
        window = self._windows.get(key, [])
        window = [t for t in window if t > cutoff]
        self._windows[key] = window

        if len(window) >= max_requests:
            # 计算重置时间
            oldest = window[0] if window else now
            reset_at = oldest + window_seconds
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_at=reset_at,
            )

        window.append(now)
        remaining = max_requests - len(window)
        return RateLimitResult(
            allowed=True,
            remaining=remaining,
            reset_at=now + window_seconds,
        )


# 预定义限流配置（安全审计 V-03）
RATE_LIMITS: dict[str, tuple[int, int]] = {
    "login": (5, 60),           # 登录: 5次/分钟
    "llm_generation": (10, 60),  # LLM生成: 10次/分钟
    "api_default": (60, 60),     # 通用API: 60次/分钟
    "data_deletion": (3, 86400),  # 数据删除: 3次/天
}


_limiter: InMemoryRateLimiter | None = None


def get_rate_limiter() -> InMemoryRateLimiter:
    """获取速率限制器单例。"""
    global _limiter
    if _limiter is None:
        _limiter = InMemoryRateLimiter()
    return _limiter
