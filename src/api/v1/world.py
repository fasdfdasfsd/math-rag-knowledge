"""世界地图 API 路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from src.api.deps import get_current_user
from src.models.schemas.common import APIResponse

router = APIRouter()


@router.get("", response_model=APIResponse[list[dict]])
async def list_worlds(
    user: dict = Depends(get_current_user),
) -> APIResponse[list[dict]]:
    """获取所有世界列表。"""
    return APIResponse(data=[
        {"id": "magic_forest", "name": "魔法森林", "status": "active"},
        {"id": "underwater", "name": "海底王国", "status": "locked"},
        {"id": "space_station", "name": "星际空间站", "status": "locked"},
    ])


@router.get("/{world_id}/chapters", response_model=APIResponse[list[dict]])
async def list_chapters(
    world_id: str,
    user: dict = Depends(get_current_user),
) -> APIResponse[list[dict]]:
    """获取世界下的章节列表。"""
    return APIResponse(data=[
        {"id": f"{world_id}_ch1", "name": "入门探索", "unlocked": True},
    ])


@router.get("/{world_id}/progress", response_model=APIResponse[dict])
async def get_world_progress(
    world_id: str,
    user: dict = Depends(get_current_user),
) -> APIResponse[dict]:
    """获取用户在世界中的整体进度。"""
    return APIResponse(data={
        "completed_count": 5,
        "total_count": 20,
        "progress_pct": 25.0,
    })
