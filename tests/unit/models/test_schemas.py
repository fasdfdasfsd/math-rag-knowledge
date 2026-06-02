"""Pydantic schema tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.models.schemas.common import DataResponse, ErrorDetail, PaginationParams, Page
from src.models.schemas.adventure import (
    LevelStartRequest,
    LevelStartResponse,
    AnswerSubmitRequest,
    AnswerSubmitResponse,
    LevelBrief,
)
from src.models.schemas.npc import NPCBrief, NPCDialogueResponse
from src.models.schemas.parent import (
    ChildProgress,
    ParentDashboardResponse,
    DataManagementRequest,
)


class TestCommonSchemas:
    def test_data_response(self) -> None:
        resp = DataResponse[str](data="hello")
        assert resp.data == "hello"
        assert resp.error is None

    def test_error_detail(self) -> None:
        err = ErrorDetail(title="Not Found", status=404, detail="Resource missing")
        assert err.status == 404
        assert err.title == "Not Found"

    def test_pagination_defaults(self) -> None:
        params = PaginationParams()
        assert params.page == 1
        assert params.page_size == 20

    def test_pagination_limits(self) -> None:
        with pytest.raises(ValidationError):
            PaginationParams(page_size=200)

    def test_page_response(self) -> None:
        page = Page[str](items=["a", "b"], total=2, page=1, page_size=20, total_pages=1)
        assert page.items == ["a", "b"]


class TestAdventureSchemas:
    def test_level_start_request(self) -> None:
        req = LevelStartRequest(level_id="l1", mode="hero")
        assert req.level_id == "l1"

    def test_answer_submit(self) -> None:
        req = AnswerSubmitRequest(level_id="l1", answer="3/4", time_spent_ms=5000)
        assert req.answer == "3/4"

    def test_level_brief(self) -> None:
        brief = LevelBrief(id="l1", name="Test", difficulty=2, state="available", stars=0, best_score=0.0)
        assert brief.state == "available"


class TestNPCSchemas:
    """NPC schema 测试 — 覆盖 npc.py (0% → 100%)."""

    def test_npc_brief_all_fields(self) -> None:
        npc = NPCBrief(id="npc_01", name="数学猫头鹰", role="mentor", avatar_url="/avatars/owl.png")
        assert npc.id == "npc_01"
        assert npc.name == "数学猫头鹰"
        assert npc.role == "mentor"
        assert npc.avatar_url == "/avatars/owl.png"

    def test_npc_brief_without_avatar(self) -> None:
        npc = NPCBrief(id="npc_02", name="数字精灵", role="guide")
        assert npc.avatar_url is None

    def test_npc_dialogue_response(self) -> None:
        resp = NPCDialogueResponse(
            npc_id="npc_01", npc_name="数学猫头鹰",
            content="你解出了这道题！让我们继续冒险吧。",
            trigger_event="level_complete",
        )
        assert resp.npc_id == "npc_01"
        assert resp.trigger_event == "level_complete"


class TestParentSchemas:
    """Parent schema 测试 — 覆盖 parent.py (0% → 100%)."""

    def test_child_progress(self) -> None:
        child = ChildProgress(
            user_id="u1", nickname="小明", grade=3,
            total_levels_completed=42, total_stars=128,
            average_score=87.5, current_world="算术大陆", current_chapter="分数进阶",
            struggling_concepts=["分数比较"], mastered_concepts=["整数四则运算", "小数基础"],
        )
        assert child.user_id == "u1"
        assert child.total_levels_completed == 42
        assert "分数比较" in child.struggling_concepts
        assert len(child.mastered_concepts) == 2

    def test_parent_dashboard_response(self) -> None:
        child = ChildProgress(
            user_id="u1", nickname="小明", grade=3,
            total_levels_completed=10, total_stars=30,
            average_score=85.0, current_world="几何山谷", current_chapter="三角形",
            struggling_concepts=[], mastered_concepts=[],
        )
        dashboard = ParentDashboardResponse(
            children=[child], weekly_active_days=5, total_learning_hours=3.5,
        )
        assert len(dashboard.children) == 1
        assert dashboard.weekly_active_days == 5

    def test_data_management_valid_actions(self) -> None:
        for action in ("export", "delete", "download_report"):
            req = DataManagementRequest(action=action, user_id="u1")
            assert req.action == action

    def test_data_management_invalid_action(self) -> None:
        with pytest.raises(ValidationError):
            DataManagementRequest(action="hack", user_id="u1")

    def test_data_management_optional_date_range(self) -> None:
        req = DataManagementRequest(action="export", user_id="u1", date_range="2026-01")
        assert req.date_range == "2026-01"

        req_no_date = DataManagementRequest(action="export", user_id="u1")
        assert req_no_date.date_range is None
