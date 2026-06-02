"""Prompt 组装器测试。"""

from __future__ import annotations

import pytest

from src.services.llm_generation.prompt_assembler import PromptAssembler


@pytest.fixture
def assembler() -> PromptAssembler:
    return PromptAssembler()


async def test_assembles_system_and_user_messages(
    assembler: PromptAssembler,
) -> None:
    """应生成 system + user 两条消息。"""
    messages = await assembler.assemble("【知识范围】分数", "3/4 + 1/2 = ?")
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert "分数" in messages[0]["content"]
    assert "3/4 + 1/2" in messages[1]["content"]


async def test_includes_level_context(assembler: PromptAssembler) -> None:
    """关卡上下文应注入 user message。"""
    messages = await assembler.assemble(
        "【难度】3",
        "开始冒险",
        level_context={"mode": "hero", "topic": "分数", "npc": "分数王子"},
    )
    assert "hero" in messages[1]["content"]
    assert "分数王子" in messages[1]["content"]


async def test_minimal_prompt(assembler: PromptAssembler) -> None:
    """空约束也应生成有效 messages。"""
    messages = await assembler.assemble("", "开始")
    assert len(messages) == 2
    assert len(messages[0]["content"]) > 0
