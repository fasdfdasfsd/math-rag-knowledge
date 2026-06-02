"""安全相关 ORM 模型：audit_logs, content_reports。"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class AuditLog(Base):
    """审计日志表（仅追加，不可修改/删除）。"""
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(50), nullable=False, index=True)   # llm_call / content_gen / user_action / ...
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    level_id = Column(UUID(as_uuid=True), nullable=True)
    detail = Column(Text, nullable=True)                           # JSON: 事件详情
    previous_hash = Column(String(64), nullable=True)              # 前一条审计记录的 SHA-256
    current_hash = Column(String(64), nullable=False)              # 本条审计记录的 SHA-256
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class ContentReport(Base):
    """内容举报表 — 用户举报问题内容。"""
    __tablename__ = "content_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reporter_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    level_id = Column(UUID(as_uuid=True), ForeignKey("levels.id", ondelete="CASCADE"), nullable=False)
    report_type = Column(String(30), nullable=False)               # wrong_answer / inappropriate / confusing / other
    description = Column(Text, nullable=True)
    status = Column(String(20), default="pending")                 # pending / reviewed / resolved / dismissed
    reviewed_by = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
