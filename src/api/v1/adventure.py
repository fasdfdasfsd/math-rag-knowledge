"""冒险关卡 API 路由 — 开始关卡 / 提交答案 / SSE 流式 / 关卡列表。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user, get_db
from src.core.exceptions import NotFoundException
from src.models.schemas.adventure import (
    AnswerSubmitRequest,
    AnswerSubmitResponse,
    LevelBrief,
    LevelStartRequest,
    LevelStartResponse,
)
from src.models.schemas.common import APIResponse

router = APIRouter()


@router.post("/levels/{level_id}/start", response_model=APIResponse[LevelStartResponse])
async def start_level(
    level_id: str,
    request: LevelStartRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[LevelStartResponse]:
    """开始指定关卡。

    委托给 Decision Engine Service → RAG Constraint Service → LLM Generation Service。
    返回关卡元数据和初始 NPC 对话。
    """
    # 委托给 Service 层（具体实现待 Service 填充后替换 TODO）
    return APIResponse(
        data=LevelStartResponse(
            level_id=level_id,
            title="冒险开始",
            description="准备进入数学冒险世界...",
            npc_dialogue="博士：准备好了吗？今天的冒险很精彩！",
            question="3/4 + 1/2 = ?",
            difficulty=2,
            hints=["试试通分", "找到公分母"],
        )
    )


@router.post("/levels/{level_id}/answer", response_model=APIResponse[AnswerSubmitResponse])
async def submit_answer(
    level_id: str,
    request: AnswerSubmitRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[AnswerSubmitResponse]:
    """提交关卡答案。

    委托给 Decision Engine Service 判定对错 → 更新用户画像 → 返回反馈。
    """
    # 规则引擎判定（简化版，后续委托给 Service）
    correct = request.answer.strip() == "5/4"
    return APIResponse(
        data=AnswerSubmitResponse(
            is_correct=correct,
            score=1.0 if correct else 0.0,
            stars=3 if correct else 0,
            explanation="5/4（1¼）是正确的！通分后 3/4+2/4=5/4。" if correct else "换个思路试试看！",
            next_level_id="level_002" if correct else None,
        )
    )


@router.get("/chapters/{chapter_id}/levels", response_model=APIResponse[list[LevelBrief]])
async def list_levels(
    chapter_id: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[list[LevelBrief]]:
    """获取章节下的关卡列表。

    委托给 Repository 层查询 → 返回用户进度和关卡摘要。
    """
    return APIResponse(
        data=[
            LevelBrief(
                id="level_001",
                name="分数王国的入口",
                difficulty=2,
                state="available",
                stars=0,
                best_score=0.0,
            ),
            LevelBrief(
                id="level_002",
                name="分数王子的挑战",
                difficulty=3,
                state="locked",
                stars=0,
                best_score=0.0,
            ),
        ]
    )


@router.get("/levels/{level_id}/stream")
async def stream_level(
    level_id: str,
    user: dict = Depends(get_current_user),
) -> dict:
    """SSE 段落级流式推送关卡内容。

    返回 StreamingResponse（非 JSON）。
    前端通过 EventSource 接收逐段内容。
    """
    try:
        # 委托给 StreamManager → LLMProvider.generate_stream()
        # TODO: 整合 Service 层后替换为真实流式调用
        raise NotFoundException("Level", level_id)
    except NotFoundException:
        raise HTTPException(status_code=404, detail=f"Level {level_id} not found")
