"""NPC repository tests."""

from __future__ import annotations

import pytest

from src.repositories.npc_repo import NPCRepository


@pytest.fixture
def repo() -> NPCRepository:
    r = NPCRepository()
    r._npcs = {
        "npc1": {"id": "npc1", "name": "Zero King", "level_ids": ["l1", "l2"]},
        "npc2": {"id": "npc2", "name": "Prince Fraction", "level_ids": ["l3"]},
    }
    return r


class TestNPCRepo:
    async def test_get_by_id(self, repo: NPCRepository) -> None:
        npc = await repo.get_by_id("npc1")
        assert npc is not None
        assert npc["name"] == "Zero King"

    async def test_get_by_level(self, repo: NPCRepository) -> None:
        npcs = await repo.get_by_level("l1")
        assert len(npcs) == 1
        assert npcs[0]["name"] == "Zero King"

    async def test_create_npc(self, repo: NPCRepository) -> None:
        npc = await repo.create_npc({"name": "Triangle Knight", "level_ids": []})
        fetched = await repo.get_by_id(npc["id"])
        assert fetched is not None

    async def test_update_dialogue(self, repo: NPCRepository) -> None:
        dialogue = await repo.update_dialogue("npc1", {"text": "Hello!", "user_id": "u1"})
        assert dialogue["text"] == "Hello!"
