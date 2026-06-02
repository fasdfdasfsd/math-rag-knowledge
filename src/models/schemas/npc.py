"""NPC Pydantic Schema。"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class NPCBrief(BaseModel):
    """NPC 摘要信息。"""
    id: str
    name: str
    role: str
    avatar_url: Optional[str] = None


class NPCDialogueResponse(BaseModel):
    """NPC 对话响应。"""
    npc_id: str
    npc_name: str
    content: str
    trigger_event: str
