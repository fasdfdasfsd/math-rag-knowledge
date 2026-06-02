"""家长仪表盘 API 路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from src.api.deps import get_current_user
from src.models.schemas.common import APIResponse

router = APIRouter()


@router.get("/dashboard", response_model=APIResponse[dict])
async def get_dashboard(
    user: dict = Depends(get_current_user),
) -> APIResponse[dict]:
    """获取家长仪表盘数据。"""
    return APIResponse(data={
        "summary": {
            "total_minutes": 185,
            "sessions_completed": 12,
            "streak_days": 5,
            "avg_accuracy": 0.72,
        },
        "mastery_heatmap": [
            {"name": "分数比较", "mastery": 0.85, "status": "green"},
            {"name": "分数乘法", "mastery": 0.45, "status": "yellow"},
        ],
        "recommendations": ["建议本周重点练习分数乘法"],
    })


@router.get("/children/{child_id}/progress", response_model=APIResponse[dict])
async def get_child_progress(
    child_id: str,
    user: dict = Depends(get_current_user),
) -> APIResponse[dict]:
    """获取单个孩子的学习进度详情。"""
    return APIResponse(data={
        "child_id": child_id,
        "current_world": "magic_forest",
        "completed_levels": 5,
    })


@router.post("/data-management", response_model=APIResponse[dict])
async def manage_data(
    user: dict = Depends(get_current_user),
) -> APIResponse[dict]:
    """数据管理操作。"""
    return APIResponse(data={"message": "数据管理功能已就绪"})
