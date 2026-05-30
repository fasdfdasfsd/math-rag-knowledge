---
category: Python生态链
priority: must
updated: 2026-05-30
---

# FastAPI 项目骨架

## 概述

FastAPI 是现代 Python Web 框架，具有高性能、自动生成 OpenAPI 文档、类型安全等特点。本规范提供标准化的 FastAPI 项目骨架，涵盖目录结构、路由组织、依赖注入、中间件、请求/响应模型和生命周期事件的最佳实践。

## 核心规则

### 🔴 必须遵守 (MUST)

1. **遵循标准项目目录结构**
   - `src/api/` — 路由层（HTTP 入口）
   - `src/services/` — 业务逻辑层
   - `src/repositories/` — 数据访问层
   - `src/models/` — 数据模型
   - `src/core/` — 核心配置和工具
   - `src/utils/` — 通用工具函数

2. **每个路由文件必须使用 APIRouter**
   - 按功能模块拆分路由
   - 每个模块有独立的 prefix 和 tags

3. **依赖注入使用 Depends**
   - 共享逻辑（认证、数据库会话）通过 Depends 注入
   - 禁止在路由函数中直接初始化依赖

### 🟡 强烈建议 (SHOULD)

1. **Pydantic 模型统一管理**
   - 请求模型：继承 `pydantic.BaseModel`
   - 响应模型：在路由装饰器中声明 `response_model`
   - 配置模型：使用 `pydantic_settings.BaseSettings`

2. **中间件配置**
   - CORS 中间件（允许跨域）
   - 日志中间件（请求/响应日志）
   - 异常处理中间件（统一错误响应格式）

3. **生命周期事件**
   - `startup`：数据库连接池初始化、缓存预热
   - `shutdown`：连接池关闭、资源清理

### 🟢 可选建议 (MAY)

1. **后台任务**
   - 使用 `BackgroundTasks` 处理异步通知
   - 使用 Celery 或 ARQ 处理重任务

2. **OpenAPI 自定义**
   - 自定义 tags metadata
   - API 版本管理

## 正确示例：完整的最小 FastAPI 应用骨架

```python
# ========== 目录结构 ==========
"""
my-project/
  src/
    __init__.py
    main.py                  # 应用入口
    core/
      __init__.py
      config.py              # 全局配置
      database.py            # 数据库连接
      exceptions.py          # 全局异常定义
      middleware.py           # 中间件
      dependencies.py         # 依赖注入
    api/
      __init__.py
      v1/
        __init__.py
        router.py            # v1 路由汇总
        users.py             # 用户模块路由
        documents.py          # 文档模块路由
        health.py             # 健康检查
    models/
      __init__.py
      user.py                # 用户模型
      document.py            # 文档模型
      common.py              # 通用模型
    services/
      __init__.py
      user_service.py        # 用户业务逻辑
      document_service.py    # 文档业务逻辑
    repositories/
      __init__.py
      user_repository.py     # 用户数据访问
      document_repository.py # 文档数据访问
    utils/
      __init__.py
      security.py            # 安全工具
      pagination.py          # 分页工具
  tests/
    __init__.py
    conftest.py
    api/
    services/
    repositories/
"""


# ========== 1. core/config.py — 全局配置 ==========

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """应用配置，从环境变量加载"""
    
    # 应用
    APP_NAME: str = "RAG API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_PREFIX: str = "/api/v1"
    
    # 数据库
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost:5432/ragdb"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # 安全
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    CORS_ALLOW_CREDENTIALS: bool = True
    
    # 缓存
    CACHE_TTL_DEFAULT: int = 300
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()


# ========== 2. core/database.py — 数据库连接 ==========

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    echo=settings.DEBUG,
)

async_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db() -> AsyncSession:
    """数据库会话依赖"""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ========== 3. core/exceptions.py — 异常定义 ==========

from fastapi import HTTPException, status


class AppException(HTTPException):
    """应用基础异常"""
    def __init__(self, status_code: int, detail: str, error_code: str = "UNKNOWN"):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code


class NotFoundException(AppException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code="NOT_FOUND",
        )


class DuplicateException(AppException):
    def __init__(self, detail: str = "Resource already exists"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            error_code="DUPLICATE",
        )


class UnauthorizedException(AppException):
    def __init__(self, detail: str = "Not authorized"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="UNAUTHORIZED",
        )


# ========== 4. core/middleware.py — 中间件 ==========

import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        logger.info(
            f"{request.method} {request.url.path} "
            f"{response.status_code} {process_time:.3f}s"
        )
        
        response.headers["X-Process-Time"] = str(process_time)
        return response


# ========== 5. models/common.py — 通用模型 ==========

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Generic, TypeVar, List

T = TypeVar("T")


class PaginationParams(BaseModel):
    """分页参数"""
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应"""
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class ErrorResponse(BaseModel):
    """统一错误响应"""
    error: str
    error_code: str
    detail: str
    timestamp: datetime = Field(default_factory=datetime.now)


# ========== 6. models/user.py — 用户模型 ==========

from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional


class UserCreate(BaseModel):
    """创建用户请求"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    """更新用户请求"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None


class UserResponse(BaseModel):
    """用户响应"""
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """用户登录请求"""
    email: EmailStr
    password: str


# ========== 7. repositories/user_repository.py ==========

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List


class UserRepository:
    """用户数据访问层"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def find_by_email(self, email: str) -> Optional[dict]:
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def find_by_id(self, user_id: int) -> Optional[dict]:
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def create(self, data: dict) -> dict:
        user = UserModel(**data)
        self.db.add(user)
        await self.db.flush()
        return user
    
    async def list(self, skip: int = 0, limit: int = 20) -> List[dict]:
        stmt = select(UserModel).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def count(self) -> int:
        stmt = select(func.count(UserModel.id))
        result = await self.db.execute(stmt)
        return result.scalar()


# ========== 8. services/user_service.py ==========

from typing import Optional, List


class UserService:
    """用户业务逻辑层"""
    
    def __init__(self, repository: UserRepository):
        self.repository = repository
    
    async def create_user(self, user_data: UserCreate) -> dict:
        existing = await self.repository.find_by_email(user_data.email)
        if existing:
            raise DuplicateException(f"Email {user_data.email} already exists")
        
        user_dict = user_data.model_dump()
        user_dict["password"] = hash_password(user_dict["password"])
        
        return await self.repository.create(user_dict)
    
    async def get_user(self, user_id: int) -> dict:
        user = await self.repository.find_by_id(user_id)
        if not user:
            raise NotFoundException(f"User {user_id} not found")
        return user


# ========== 9. api/v1/health.py ==========

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "timestamp": datetime.now().isoformat(),
    }


# ========== 10. api/v1/users.py ==========

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

router = APIRouter(prefix="/users", tags=["users"])


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """用户服务依赖注入"""
    repository = UserRepository(db)
    return UserService(repository)


@router.post("", response_model=UserResponse, status_code=201)
async def create_user(
    user_data: UserCreate,
    service: UserService = Depends(get_user_service),
):
    """创建用户"""
    return await service.create_user(user_data)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
):
    """获取用户"""
    return await service.get_user(user_id)


@router.get("", response_model=PaginatedResponse[UserResponse])
async def list_users(
    params: PaginationParams = Depends(),
    service: UserService = Depends(get_user_service),
):
    """用户列表"""
    items = await service.repository.list(
        skip=(params.page - 1) * params.page_size,
        limit=params.page_size,
    )
    total = await service.repository.count()
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=params.page,
        page_size=params.page_size,
        total_pages=(total + params.page_size - 1) // params.page_size,
    )


# ========== 11. api/v1/router.py — 路由汇总 ==========

from fastapi import APIRouter

v1_router = APIRouter(prefix="/api/v1")

# 注册子路由
v1_router.include_router(health.router)
v1_router.include_router(users.router)
v1_router.include_router(documents.router)


# ========== 12. main.py — 应用入口 ==========

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    # startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    yield
    # shutdown
    await engine.dispose()
    logger.info("Application shutdown")


def create_app() -> FastAPI:
    """应用工厂"""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        lifespan=lifespan,
        docs_url="/docs" if settings.DEBUG else None,
    )
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 日志中间件
    app.add_middleware(LoggingMiddleware)
    
    # 全局异常处理
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error=exc.error_code,
                detail=exc.detail,
            ).model_dump(),
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.exception(f"Unhandled exception: {exc}")
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="INTERNAL_ERROR",
                detail="An internal error occurred",
            ).model_dump(),
        )
    
    # 注册路由
    app.include_router(v1_router)
    
    return app


app = create_app()
```

## 错误示例

```python
# 错误 1：所有路由写在一个文件

# 错误：单文件路由（app.py 包含所有路由）
@app.get("/users")
async def list_users(): ...

@app.post("/users")  
async def create_user(): ...

@app.get("/documents")
async def list_documents(): ...

@app.post("/documents")
async def create_document(): ...
# 文件膨胀到上千行，难以维护


# 错误 2：不使用 APIRouter

# 错误直接在 app 上注册
# 没有 prefix，没有 tags
# 无法独立版本管理


# 错误 3：路由函数中初始化依赖

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    # 错误：在路由中初始化数据库
    db = SessionLocal()  # 手动管理会话
    repo = UserRepository(db)
    service = UserService(repo)
    
    try:
        return await service.get_user(user_id)
    finally:
        db.close()
# 应使用 Depends 注入


# 错误 4：不使用 Pydantic response_model

@app.post("/users")
async def create_user(user_data: UserCreate):
    user = await service.create_user(user_data)
    return user  # 可能泄露密码等敏感字段
# 应声明 response_model=UserResponse


# 错误 5：没有全局异常处理

# 到处 try-except，错误响应格式不统一
try:
    user = await service.get_user(user_id)
except Exception as e:
    return {"error": str(e)}  # 格式不一致
```

## 工具链配置

```toml
# [tool.ruff] 配置 (参考 04-Python生态链/02-Ruff代码检查.md)
# [tool.mypy] 配置 (参考 04-Python生态链/04-mypy类型检查.md)

# server 启动
# uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

## 参考来源

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [FastAPI 项目结构最佳实践](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
- [Pydantic 文档](https://docs.pydantic.dev/)
