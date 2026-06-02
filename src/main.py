"""FastAPI 应用工厂 — 数学冒险世界后端入口。"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.v1 import (
    adventure,
    collection,
    content,
    npc,
    parent,
    push,
    world,
)
from src.core.config import get_settings
from src.core.database import init_db, shutdown_db
from src.core.middleware import register_middleware
from src.utils.structured_logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """应用生命周期：启动时初始化连接池/关闭时清理。"""
    settings = get_settings()
    logger.info("app.starting", app_name=settings.APP_NAME, version=settings.APP_VERSION)
    await init_db(settings)
    yield
    await shutdown_db(settings)
    logger.info("app.stopped", app_name=settings.APP_NAME)


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例并注册路由与中间件。"""
    settings = get_settings()
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="数学冒险世界后端 API — 面向小学数学的 RAG 驱动游戏化学习平台",
        lifespan=lifespan,
    )

    # 注册中间件（顺序敏感：后注册的先执行）
    register_middleware(app)

    # 注册路由
    app.include_router(adventure.router, prefix="/api/v1/adventure", tags=["adventure"])
    app.include_router(npc.router, prefix="/api/v1/npc", tags=["npc"])
    app.include_router(collection.router, prefix="/api/v1/collection", tags=["collection"])
    app.include_router(parent.router, prefix="/api/v1/parent", tags=["parent"])
    app.include_router(world.router, prefix="/api/v1/world", tags=["world"])
    app.include_router(content.router, prefix="/api/v1/content", tags=["content"])
    app.include_router(push.router, prefix="/api/v1/push", tags=["push"])

    @app.get("/health", tags=["system"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok", "app": settings.APP_NAME}

    return app


app = create_app()
