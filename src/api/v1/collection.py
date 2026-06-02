"""收藏 API 路由 — NPC 角色卡片收集。"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from src.api.deps import get_current_user
from src.models.schemas.common import APIResponse

router = APIRouter()


@router.get("", response_model=APIResponse[dict])
async def list_favorites(
    user: dict = Depends(get_current_user),
) -> APIResponse[dict]:
    """获取用户的 NPC 角色收藏列表。"""
    return APIResponse(data={
        "total": 30,
        "collected": 5,
        "items": [
            {"npc_id": "fraction_prince", "name": "分数王子", "collected_at": "2026-05-20"},
            {"npc_id": "zero_king", "name": "零国王", "collected_at": "2026-05-18"},
        ],
    })


@router.post("/{level_id}", response_model=APIResponse[dict])
async def favorite_level(
    level_id: str,
    user: dict = Depends(get_current_user),
) -> APIResponse[dict]:
    """收藏关卡（完成关卡的 NPC 角色卡片）。"""
    return APIResponse(data={"status": "collected", "level_id": level_id})


@router.delete("/{level_id}", response_model=APIResponse[dict])
async def unfavorite_level(
    level_id: str,
    user: dict = Depends(get_current_user),
) -> APIResponse[dict]:
    """取消收藏。"""
    return APIResponse(data={"status": "removed", "level_id": level_id})
