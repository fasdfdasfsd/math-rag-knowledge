"""Adventure repository tests."""

from __future__ import annotations

import pytest

from src.repositories.adventure_repo import AdventureRepository


@pytest.fixture
def repo() -> AdventureRepository:
    r = AdventureRepository()
    r._levels = {
        "l1": {"id": "l1", "chapter_id": "ch1", "name": "Forest Entrance"},
        "l2": {"id": "l2", "chapter_id": "ch1", "name": "River Crossing"},
        "l3": {"id": "l3", "chapter_id": "ch2", "name": "Mountain Path"},
    }
    r._chapters = {
        "ch1": {"id": "ch1", "world_id": "w1", "name": "Magic Forest"},
        "ch2": {"id": "ch2", "world_id": "w1", "name": "Dark Cave"},
    }
    return r


class TestAdventureRepo:
    async def test_get_level_by_id(self, repo: AdventureRepository) -> None:
        level = await repo.get_level_by_id("l1")
        assert level is not None
        assert level["name"] == "Forest Entrance"

    async def test_get_levels_by_chapter(self, repo: AdventureRepository) -> None:
        levels = await repo.get_levels_by_chapter("ch1")
        assert len(levels) == 2

    async def test_create_level(self, repo: AdventureRepository) -> None:
        new_level = await repo.create_level({"name": "Test Level", "chapter_id": "ch3"})
        assert new_level["name"] == "Test Level"
        fetched = await repo.get_level_by_id(new_level["id"])
        assert fetched is not None

    async def test_update_level(self, repo: AdventureRepository) -> None:
        await repo.update_level("l1", {"name": "Updated"})
        level = await repo.get_level_by_id("l1")
        assert level["name"] == "Updated"

    async def test_get_chapters_by_world(self, repo: AdventureRepository) -> None:
        chapters = await repo.get_chapters_by_world("w1")
        assert len(chapters) == 2
