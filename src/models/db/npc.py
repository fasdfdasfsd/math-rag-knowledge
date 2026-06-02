"""NPC 相关 ORM 模型：npcs, npc_dialogues。"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class NPC(Base):
    """NPC 表 — 冒险世界中的非玩家角色。"""
    __tablename__ = "npcs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    role = Column(String(50), nullable=True)              # guide / merchant / quiz_master / ...
    avatar_url = Column(String(500), nullable=True)
    personality = Column(Text, nullable=True)              # JSON: 性格特质描述
    background_story = Column(Text, nullable=True)
    grade_min = Column(Integer, nullable=True)             # 现身最低年级
    grade_max = Column(Integer, nullable=True)             # 现身最高年级
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class NPCDialogue(Base):
    """NPC 对话表 — NPC 在特定关卡中的对话内容。"""
    __tablename__ = "npc_dialogues"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    npc_id = Column(UUID(as_uuid=True), ForeignKey("npcs.id", ondelete="CASCADE"), nullable=False, index=True)
    level_id = Column(UUID(as_uuid=True), ForeignKey("levels.id", ondelete="CASCADE"), nullable=False, index=True)
    trigger_event = Column(String(50), nullable=False)    # level_start | level_complete | hint_request | ...
    content = Column(Text, nullable=False)                 # 对话文本（可含变量占位符）
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
