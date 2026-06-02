"""全局中间件 — 请求日志 / CORS / 异常处理。"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from .exceptions import AppException


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件 — 记录 trace_id 和请求耗时。"""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        trace_id = str(uuid.uuid4())[:8]
        request.state.trace_id = trace_id
        request.state.start_time = time.time()

        response = await call_next(request)

        duration_ms = (time.time() - request.state.start_time) * 1000
        response.headers["X-Trace-Id"] = trace_id
        response.headers["X-Duration-Ms"] = str(int(duration_ms))

        return response


class ExceptionHandlingMiddleware(BaseHTTPMiddleware):
    """全局异常处理中间件 — AppException → RFC 9457 JSON 响应。"""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        try:
            return await call_next(request)
        except AppException as exc:
            trace_id = getattr(request.state, "trace_id", "")
            problem_detail = {
                "type": "about:blank",
                "title": exc.message,
                "status": exc.status_code,
                "detail": exc.detail,
                "trace_id": trace_id,
            }
            return JSONResponse(
                status_code=exc.status_code,
                content=problem_detail,
                media_type="application/problem+json",
            )


def register_middleware(app: FastAPI) -> None:
    """注册所有全局中间件（顺序敏感：后注册的先执行）。"""
    # CORS — MVP 阶段允许 localhost 开发
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
    )

    # 异常处理（后注册 = 外圈，最先捕获异常）
    app.add_middleware(ExceptionHandlingMiddleware)

    # 请求日志
    app.add_middleware(RequestLoggingMiddleware)
