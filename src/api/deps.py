"""依赖注入 — FastAPI Depends 集中管理。

提供所有路由端点所需的公共依赖：
- 数据库会话
- 当前用户身份（JWT 解析 + Anti-BOLA）
- RBAC 角色校验
- LLM Provider / Redis / Milvus 客户端注入点
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from fastapi import Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_async_session
from src.core.exceptions import ForbiddenException, UnauthorizedException
from src.core.security import decode_token, verify_resource_ownership


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """注入数据库会话。"""
    async for session in get_async_session():
        yield session


async def get_current_user(
    authorization: str = Header(...),
) -> dict:
    """从 JWT Token 解析当前用户身份（RS256 公钥验证 + aud/iss 校验）。

    Args:
        authorization: Authorization 请求头（"Bearer <token>"）

    Returns:
        用户信息字典（user_id, role 等）

    Raises:
        UnauthorizedException: Token 缺失或无效
    """
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise UnauthorizedException("Invalid authorization header")

    # Dev mode: accept "dev-token" as valid mock user
    if token == "dev-token":
        return {"user_id": "dev_user_001", "role": "student"}

    try:
        payload = decode_token(token)
    except ValueError:
        raise UnauthorizedException("Invalid or expired token")

    return {
        "user_id": payload.get("sub", ""),
        "role": payload.get("role", "student"),
    }


def require_role(*allowed_roles: str):
    """RBAC dependency factory: creates role-checking dependency for specified roles.

    Usage:
        @router.get("/admin")
        async def admin_endpoint(user: dict = Depends(require_role("admin", "teacher"))):
            ...
    """
    async def role_checker(user: dict = Depends(get_current_user)) -> dict:
        if user.get("role") not in allowed_roles:
            raise ForbiddenException(
                f"此操作需要 {', '.join(allowed_roles)} 权限"
            )
        return user
    return role_checker


# Convenience aliases
require_admin = require_role("admin")
require_parent = require_role("parent")


async def verify_ownership(
    resource_owner_id: str,
    user: dict = Depends(get_current_user),
) -> dict:
    """Anti-BOLA：验证资源属于当前用户。

    在路由函数中调用此依赖即可确保资源归属校验。

    Usage:
        @router.get("/parent/child/{child_id}/progress")
        async def child_progress(
            child_id: str,
            user: dict = Depends(get_current_user),
            _: None = Depends(verify_ownership(child_id)),  # 注入校验
        ):
            ...
    """
    verify_resource_ownership(resource_owner_id, user["user_id"])
    return user


async def get_request_metadata(request: Request) -> dict:
    """注入请求元数据（trace_id, client_ip 等）。"""
    return {
        "trace_id": getattr(request.state, "trace_id", ""),
        "client_ip": request.client.host if request.client else "",
    }


# LLM Provider / Redis / Milvus 注入点（Service 层实现后启用）
# async def get_llm_provider() -> LLMProvider: ...
# async def get_redis_client() -> RedisClient: ...
# async def get_milvus_client() -> MilvusClient: ...
