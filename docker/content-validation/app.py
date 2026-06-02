"""Content Validation Service — ADR-SEC-006 独立部署。
轻量级 FastAPI 应用，仅依赖 fastapi/pydantic，不引入项目全量依赖。
"""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(
    title="Content Validation Service",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
)


class HealthResponse(BaseModel):
    status: str
    service: str


@app.get("/health", tags=["system"])
async def health_check() -> HealthResponse:
    return HealthResponse(status="healthy", service="content-validation")


class ValidateRequest(BaseModel):
    content: str
    level_id: str | None = None


class ValidateResponse(BaseModel):
    passed: bool
    violations: list[str] = []
    risk_level: str = "low"  # low / medium / high / blocked


@app.post("/validate", tags=["validation"])
async def validate_content(req: ValidateRequest) -> ValidateResponse:
    """Pre-LLM / Post-LLM 内容安全审核入口。

    当前为轻量实现，后续可集成完整的 PreLLMSanitizer / PostLLMAuditor。
    """
    violations: list[str] = []

    # 基础安全检查
    if not req.content or not req.content.strip():
        violations.append("empty_content")

    # 长度限制
    if len(req.content) > 100_000:
        violations.append("content_too_long")

    if violations:
        return ValidateResponse(passed=False, violations=violations, risk_level="blocked")

    return ValidateResponse(passed=True, violations=[], risk_level="low")
