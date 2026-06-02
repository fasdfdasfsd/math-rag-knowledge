"""内容举报 API 路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from src.api.deps import get_current_user
from src.models.schemas.common import APIResponse

router = APIRouter()


@router.post("/reports", response_model=APIResponse[dict])
async def report_content(
    level_id: str,
    report_type: str,
    description: str | None = None,
    user: dict = Depends(get_current_user),
) -> APIResponse[dict]:
    """举报关卡内容问题。"""
    return APIResponse(data={
        "report_id": f"rpt_{level_id}",
        "status": "received",
        "message": "感谢反馈！我们将在24小时内审核",
    })


@router.get("/reports", response_model=APIResponse[list[dict]])
async def list_reports(
    user: dict = Depends(get_current_user),
) -> APIResponse[list[dict]]:
    """获取举报列表（管理员功能）。"""
    return APIResponse(data=[])


@router.patch("/reports/{report_id}", response_model=APIResponse[dict])
async def review_report(
    report_id: str,
    action: str,
    user: dict = Depends(get_current_user),
) -> APIResponse[dict]:
    """审核举报（管理员）。"""
    return APIResponse(data={"report_id": report_id, "status": action})
