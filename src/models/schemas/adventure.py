"""冒险/关卡 Pydantic Schema。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class LevelStartRequest(BaseModel):
    """开始关卡请求。"""
    level_id: str
    mode: str | None = None


class LevelStartResponse(BaseModel):
    """开始关卡响应。"""
    level_id: str
    title: str
    description: str
    npc_dialogue: str | None = None
    question: str
    difficulty: int
    hints: list[str] = Field(default_factory=list)


class AnswerSubmitRequest(BaseModel):
    """提交答案请求。"""
    level_id: str
    answer: str
    time_spent_ms: int = 0


class AnswerSubmitResponse(BaseModel):
    """提交答案响应。"""
    is_correct: bool
    score: float
    stars: int
    explanation: str
    next_level_id: str | None = None


class LevelBrief(BaseModel):
    """关卡摘要（用于列表展示）。"""
    id: str
    name: str
    difficulty: int
    state: str          # locked / available / in_progress / completed / perfected
    stars: int
    best_score: float
