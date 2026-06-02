"""知识相关 ORM 模型：knowledge_concepts, knowledge_relations, curriculum_standards。"""

from __future__ import annotations

from datetime import datetime
import uuid

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class KnowledgeConcept(Base):
    """知识点表 — 小学数学知识点原子单元。"""
    __tablename__ = "knowledge_concepts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    grade = Column(Integer, nullable=False)           # 适用年级
    difficulty_level = Column(Integer, default=1)     # 难度等级 1-5
    category = Column(String(50), nullable=True)      # 分类（数与代数/图形几何/...）
    tags = Column(Text, nullable=True)                # JSON 标签数组
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class KnowledgeRelation(Base):
    """知识点关系表 — 前置依赖/关联/扩展关系。"""
    __tablename__ = "knowledge_relations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_concepts.id", ondelete="CASCADE"), nullable=False, index=True)
    target_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_concepts.id", ondelete="CASCADE"), nullable=False, index=True)
    relation_type = Column(String(30), nullable=False)  # prerequisite | related | extends
    weight = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class CurriculumStandard(Base):
    """教学大纲标准表 — 各年级各章节的大纲要求。"""
    __tablename__ = "curriculum_standards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    grade = Column(Integer, nullable=False)
    chapter_id = Column(UUID(as_uuid=True), ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False)
    concept_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_concepts.id", ondelete="CASCADE"), nullable=False)
    requirement_level = Column(String(20), default="master")  # understand | master | apply
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
