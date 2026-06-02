"""自定义异常基类 — 统一异常处理体系。"""

from __future__ import annotations

from typing import Any


class AppException(Exception):
    """应用异常基类。

    所有业务异常继承此类，由全局异常处理中间件统一捕获。
    """

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        detail: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.detail = detail or {}
        super().__init__(self.message)


class NotFoundException(AppException):
    """资源不存在异常 (404)。"""

    def __init__(self, resource: str, resource_id: str) -> None:
        super().__init__(
            message=f"{resource} not found: {resource_id}",
            status_code=404,
            detail={"resource": resource, "resource_id": resource_id},
        )


class ValidationException(AppException):
    """参数校验异常 (422)。"""

    def __init__(self, message: str, errors: list[dict] | None = None) -> None:
        super().__init__(
            message=message,
            status_code=422,
            detail={"errors": errors or []},
        )


class UnauthorizedException(AppException):
    """未授权异常 (401)。"""

    def __init__(self, message: str = "Authentication required") -> None:
        super().__init__(message=message, status_code=401)


class ForbiddenException(AppException):
    """禁止访问异常 (403)。"""

    def __init__(self, message: str = "Insufficient permissions") -> None:
        super().__init__(message=message, status_code=403)


class RateLimitException(AppException):
    """速率限制异常 (429)。"""

    def __init__(self, retry_after: int = 60) -> None:
        super().__init__(
            message="Too many requests",
            status_code=429,
            detail={"retry_after_seconds": retry_after},
        )


class LLMServiceException(AppException):
    """LLM 服务调用异常 (502)。"""

    def __init__(self, provider: str, reason: str) -> None:
        super().__init__(
            message=f"LLM service error from {provider}: {reason}",
            status_code=502,
            detail={"provider": provider, "reason": reason},
        )


class ContentSafetyException(AppException):
    """内容安全拒绝异常 (451)。"""

    def __init__(self, reason: str) -> None:
        super().__init__(
            message=f"Content rejected by safety filter: {reason}",
            status_code=451,
            detail={"reason": reason},
        )
