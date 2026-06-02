"""通用 Pydantic Schema — 分页/错误/统一响应信封。"""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """RFC 9457 Problem Details 错误响应体。"""
    type: str = "about:blank"
    title: str
    status: int
    detail: str
    trace_id: str = Field(default="", description="请求追踪 ID")
    instance: str | None = None


class DataResponse(BaseModel, Generic[T]):
    """统一成功响应信封。"""
    data: T
    error: None = None


class ErrorResponse(BaseModel):
    """统一错误响应信封。"""
    data: None = None
    error: ErrorDetail


class PaginationParams(BaseModel):
    """分页参数。"""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class Page(BaseModel, Generic[T]):
    """分页响应。"""
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int


# 别名（与 API 路由层统一命名）
APIResponse = DataResponse
APIError = ErrorDetail
