"""冒险/关卡数据访问层。"""

from __future__ import annotations


class AdventureRepository:
    """关卡与冒险数据操作（MVP 内存存储）。"""

    def __init__(self) -> None:
        self._levels: dict[str, dict] = {}
        self._chapters: dict[str, dict] = {}

    async def get_level_by_id(self, level_id: str) -> dict | None:
        return self._levels.get(level_id)

    async def get_levels_by_chapter(self, chapter_id: str) -> list[dict]:
        return [l for l in self._levels.values() if l.get("chapter_id") == chapter_id]

    async def create_level(self, data: dict) -> dict:
        lid = data.get("id", f"level_{len(self._levels)+1}")
        data["id"] = lid
        self._levels[lid] = data
        return data

    async def update_level(self, level_id: str, data: dict) -> dict:
        if level_id in self._levels:
            self._levels[level_id].update(data)
        return self._levels.get(level_id, {})

    async def get_chapters_by_world(self, world_id: str) -> list[dict]:
        return [c for c in self._chapters.values() if c.get("world_id") == world_id]
