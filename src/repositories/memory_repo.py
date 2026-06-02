"""学生记忆数据访问层。"""

from __future__ import annotations


class MemoryRepository:
    """学生记忆数据操作（MVP 内存存储，后续迁移到 Redis+PG）。"""

    def __init__(self) -> None:
        self._mistakes: dict[str, list[dict]] = {}
        self._mastered: dict[str, list[str]] = {}
        self._struggling: dict[str, list[str]] = {}
        self._summaries: dict[str, str] = {}

    async def get_recent_mistakes(self, user_id: str, limit: int = 10) -> list[dict]:
        return self._mistakes.get(user_id, [])[-limit:]

    async def get_mastered_concepts(self, user_id: str) -> list[str]:
        return self._mastered.get(user_id, [])

    async def get_struggling_concepts(self, user_id: str) -> list[str]:
        return self._struggling.get(user_id, [])

    async def update_memory(self, user_id: str, session_id: str, data: dict) -> None:
        if "mistakes" in data:
            self._mistakes.setdefault(user_id, []).extend(data["mistakes"])
        if "mastered" in data:
            self._mastered[user_id] = data["mastered"]
        if "struggling" in data:
            self._struggling[user_id] = data["struggling"]

    async def get_last_session_summary(self, user_id: str) -> str | None:
        return self._summaries.get(user_id)
