"""记忆相关 ORM 模型：student_memories（持久化到 PG，活跃数据在 Redis）。"""

from __future__ import annotations

from datetime import datetime
import uuid

from sqlalchemy import Column, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class StudentMemory(Base):
    """学生记忆表 — 学习行为的持久化记录。

    注意：活跃会话的记忆数据存放在 Redis（由 memory_repo 管理），
    此表作为冷存储/分析用途。
    """
    __tablename__ = "student_memories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(64), nullable=False)
    memory_type = Column(String(30), nullable=False)      # mistake | mastered | struggling | summary
    concept_id = Column(UUID(as_uuid=True), nullable=True)
    content = Column(Text, nullable=True)                  # JSON: 记忆数据
    confidence = Column(Float, default=0.0)                # 掌握度 0-1
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)           # 记忆过期时间
