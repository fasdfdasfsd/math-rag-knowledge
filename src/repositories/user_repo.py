"""用户数据访问层。"""

from __future__ import annotations


class UserRepository:
    """用户数据操作（MVP 内存存储，后续迁移到 PostgreSQL）。"""

    def __init__(self) -> None:
        self._users: dict[str, dict] = {}
        self._progress: dict[str, dict] = {}  # key: user_id:level_id

    async def get_by_id(self, user_id: str) -> dict | None:
        return self._users.get(user_id)

    async def get_by_email(self, email: str) -> dict | None:
        for u in self._users.values():
            if u.get("email") == email:
                return u
        return None

    async def create(self, data: dict) -> dict:
        uid = data.get("id", f"user_{len(self._users)+1}")
        data["id"] = uid
        self._users[uid] = data
        return data

    async def update(self, user_id: str, data: dict) -> dict:
        if user_id in self._users:
            self._users[user_id].update(data)
        return self._users.get(user_id, {})

    async def update_progress(self, user_id: str, level_id: str, score: float) -> None:
        key = f"{user_id}:{level_id}"
        self._progress[key] = {"score": score, "completed_at": None}
