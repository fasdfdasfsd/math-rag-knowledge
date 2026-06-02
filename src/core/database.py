"""PostgreSQL 连接池管理 — 基于 SQLAlchemy async engine。"""

from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import AsyncAdaptedQueuePool

from src.core.config import Settings

_engine = None
_async_session_maker = None


async def init_db(settings: Settings) -> None:
    """初始化数据库连接池。"""
    global _engine, _async_session_maker  # noqa: PLW0603

    _engine = create_async_engine(
        settings.db_url,
        echo=settings.DB_ECHO,
        poolclass=AsyncAdaptedQueuePool,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_pre_ping=True,
    )

    _async_session_maker = async_sessionmaker(
        _engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def shutdown_db(settings: Settings) -> None:
    """关闭数据库连接池。"""
    global _engine, _async_session_maker  # noqa: PLW0603

    if _engine:
        await _engine.dispose()
        _engine = None
        _async_session_maker = None


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """获取异步数据库会话（用于 FastAPI Depends）。"""
    if _async_session_maker is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")

    async with _async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
