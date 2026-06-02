"""NPC API 路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from src.api.deps import get_current_user
from src.models.schemas.common import APIResponse

router = APIRouter()


@router.get("/{npc_id}", response_model=APIResponse[dict])
async def get_npc(
    npc_id: str,
    user: dict = Depends(get_current_user),
) -> APIResponse[dict]:
    """获取 NPC 基本信息。"""
    return APIResponse(data={
        "id": npc_id,
        "name": "分数王子",
        "title": "分数王国的守护者",
        "personality": ["热情", "骄傲", "急性子"],
        "catchphrase": "分数是公平的！",
    })


@router.get("/level/{level_id}/dialogues", response_model=APIResponse[list[dict]])
async def get_npc_dialogues(
    level_id: str,
    user: dict = Depends(get_current_user),
) -> APIResponse[list[dict]]:
    """获取关卡中的 NPC 对话。"""
    return APIResponse(data=[
        {"speaker": "博士", "text": f"欢迎来到 {level_id}！"},
    ])
