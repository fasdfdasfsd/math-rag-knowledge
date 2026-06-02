"""冒险相关 ORM 模型：worlds, chapters, levels, level_content_cache。"""

from __future__ import annotations

from datetime import datetime
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class World(Base):
    """世界表 — 冒险世界的顶层容器。"""
    __tablename__ = "worlds"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    grade_range = Column(String(20), nullable=True)    # "1-2" | "3-4" | "5-6"
    theme = Column(String(100), nullable=True)          # 主题（童话/太空/...）
    sort_order = Column(Integer, default=0)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class Chapter(Base):
    """章节表 — 世界下的章节单元。"""
    __tablename__ = "chapters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    world_id = Column(UUID(as_uuid=True), ForeignKey("worlds.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    sort_order = Column(Integer, default=0)
    min_level = Column(Integer, default=1)              # 推荐最低年级
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class Level(Base):
    """关卡表 — 游戏关卡，包含题目配置和剧情数据。"""
    __tablename__ = "levels"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chapter_id = Column(UUID(as_uuid=True), ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    difficulty = Column(Integer, default=1)              # 1-5
    mode = Column(String(30), default="practice")        # practice / challenge / review / new_concept
    concept_ids = Column(Text, nullable=True)             # JSON: 关联知识点 ID 列表
    npc_ids = Column(Text, nullable=True)                 # JSON: 关联 NPC ID 列表
    sort_order = Column(Integer, default=0)
    is_generated = Column(Integer, default=0)             # 是否已生成（预生成或实时）
    generated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class LevelContentCache(Base):
    """关卡内容缓存表 — 预生成/已生成的关卡内容缓存。"""
    __tablename__ = "level_content_cache"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    level_id = Column(UUID(as_uuid=True), ForeignKey("levels.id", ondelete="CASCADE"), nullable=False, index=True)
    content_type = Column(String(30), nullable=False)    # question | story | npc_dialogue
    content = Column(Text, nullable=False)
    checksum = Column(String(64), nullable=False)        # 内容哈希
    expires_at = Column(DateTime, nullable=True)          # 过期时间（预生成内容 72h 过期）
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
