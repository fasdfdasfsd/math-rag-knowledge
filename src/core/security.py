"""安全模块 — JWT RS256 令牌管理 / bcrypt 密码哈希 / Anti-BOLA 验证。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import bcrypt

from jose import JWTError, jwt

from src.core.config import get_settings
from src.core.exceptions import ForbiddenException


def hash_password(password: str) -> str:
    """Hash password with bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against bcrypt hash."""
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def _load_private_key(key: str) -> str:
    """加载 RS256 私钥——支持 PEM 字符串或文件路径。"""
    if key.startswith("-----BEGIN"):
        return key
    with open(key) as f:
        return f.read()


def _load_public_key(key: str) -> str:
    """加载 RS256 公钥。"""
    if key.startswith("-----BEGIN"):
        return key
    with open(key) as f:
        return f.read()


def create_access_token(
    user_id: str,
    role: str,
    expires_delta: timedelta | None = None,
) -> str:
    """创建 JWT Access Token（RS256 非对称签名）。"""
    settings = get_settings()
    to_encode = {
        "sub": user_id,
        "role": role,
        "type": "access",
        "iss": "math-adventure-backend",
        "aud": "math-adventure-api",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc)
        + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)),
    }
    private_key = _load_private_key(settings.JWT_PRIVATE_KEY)
    return jwt.encode(to_encode, private_key, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """创建 JWT Refresh Token（RS256 非对称签名）。"""
    settings = get_settings()
    to_encode = {
        "sub": user_id,
        "type": "refresh",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc)
        + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    }
    private_key = _load_private_key(settings.JWT_PRIVATE_KEY)
    return jwt.encode(to_encode, private_key, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """解码并验证 JWT Token（RS256 公钥验证）。"""
    settings = get_settings()
    try:
        public_key = _load_public_key(settings.JWT_PUBLIC_KEY)
        payload = jwt.decode(
            token,
            public_key,
            algorithms=[settings.JWT_ALGORITHM],
            audience="math-adventure-api",
            issuer="math-adventure-backend",
            options={"verify_exp": True, "verify_iat": True},
        )
        return payload
    except JWTError:
        raise ValueError("Invalid or expired token")


def verify_resource_ownership(requested_user_id: str, token_user_id: str) -> None:
    """Anti-BOLA：验证请求的资源属于当前用户。

    Raises:
        ForbiddenException: 如果资源不属于当前用户
    """
    if requested_user_id != token_user_id:
        raise ForbiddenException("Resource does not belong to the current user")
