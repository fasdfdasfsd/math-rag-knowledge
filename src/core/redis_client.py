"""Redis 客户端封装 — 缓存/会话/限流。"""

from __future__ import annotations

from redis.asyncio import ConnectionPool, Redis

from src.core.config import get_settings


class RedisClient:
    """Redis 客户端封装。

    管理 Redis 异步连接池。
    用于：Embedding 缓存、学生记忆缓存、速率限制计数器。
    """

    def __init__(self) -> None:
        self._pool: ConnectionPool | None = None
        self._client: Redis | None = None

    async def connect(self) -> None:
        """初始化 Redis 连接池。"""
        if self._client is not None:
            return
        settings = get_settings()
        self._pool = ConnectionPool.from_url(
            settings.redis_url,
            decode_responses=True,
            max_connections=20,
        )
        self._client = Redis(connection_pool=self._pool)

    async def disconnect(self) -> None:
        """关闭 Redis 连接池。"""
        if self._client:
            await self._client.aclose()
            self._client = None

    @property
    def client(self) -> Redis:
        """获取 Redis 异步连接。"""
        if self._client is None:
            raise RuntimeError("Redis not connected. Call connect() first.")
        return self._client
