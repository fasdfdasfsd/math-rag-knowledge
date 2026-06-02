"""记忆组装器 — 从 Redis 查询学生近期学习记忆并组装为上下文。"""

from __future__ import annotations


class MemoryAssembler:
    """学生记忆组装器。

    从 Redis 缓存中检索学生近期学习记忆，
    为 RAG 约束层提供个性化上下文。
    """

    def __init__(self) -> None:
        self._store: dict[str, dict] = {}  # MVP: 内存存储，后续迁移到 Redis

    async def assemble_memory(
        self, user_id: str, session_id: str | None = None,
    ) -> dict:
        """组装学生记忆上下文。

        Args:
            user_id: 学生用户 ID
            session_id: 当前会话 ID

        Returns:
            包含记忆数据的字典
        """
        data = self._store.get(user_id, {})
        return {
            "recent_mistakes": data.get("mistakes", []),
            "mastered_concepts": data.get("mastered", []),
            "struggling_concepts": data.get("struggling", []),
            "last_session_summary": data.get("last_summary"),
        }

    async def update_memory(
        self, user_id: str, session_id: str, new_data: dict,
    ) -> None:
        """更新学生记忆（每次关卡完成后调用）。

        Args:
            user_id: 学生用户 ID
            session_id: 会话 ID
            new_data: 新数据 {"correct": [...], "incorrect": [...], "summary": str}
        """
        existing = self._store.get(user_id, {})

        # 合并错误记录
        mistakes = existing.get("mistakes", [])
        mistakes.extend(new_data.get("incorrect", []))
        existing["mistakes"] = mistakes[-50:]  # 保留最近 50 条

        # 合并已掌握
        mastered = set(existing.get("mastered", []))
        mastered.update(new_data.get("correct", []))
        existing["mastered"] = list(mastered)

        # 更新薄弱点
        struggling = set(existing.get("struggling", []))
        if new_data.get("incorrect"):
            struggling.update(new_data["incorrect"])
        # 正确后移出薄弱（独立于 incorrect 检查）
        if new_data.get("correct"):
            struggling.difference_update(new_data["correct"])
        existing["struggling"] = list(struggling)

        if new_data.get("summary"):
            existing["last_summary"] = new_data["summary"]

        self._store[user_id] = existing
