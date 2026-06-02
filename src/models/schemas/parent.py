"""家长仪表盘 Pydantic Schema。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ChildProgress(BaseModel):
    """孩子学习进度概览。"""
    user_id: str
    nickname: str
    grade: int
    total_levels_completed: int
    total_stars: int
    average_score: float
    current_world: str
    current_chapter: str
    struggling_concepts: list[str]
    mastered_concepts: list[str]


class ParentDashboardResponse(BaseModel):
    """家长仪表盘响应。"""
    children: list[ChildProgress]
    weekly_active_days: int
    total_learning_hours: float


class DataManagementRequest(BaseModel):
    """数据管理请求。"""
    action: str = Field(..., pattern="^(export|delete|download_report)$")
    user_id: str
    date_range: str | None = None
