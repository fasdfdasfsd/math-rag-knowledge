"""知识点选择器 — 基于掌握度和前置依赖选择考察知识点。"""

from __future__ import annotations


class KnowledgeSelector:
    """知识点选择器。

    从知识图谱中筛选适合当前学生水平和关卡的知识点。
    结合教学大纲进度、学生薄弱项、前置依赖进行选择。
    """

    async def select_for_level(
        self,
        user_id: str,
        chapter_id: str,
        difficulty_level: int,
        exclude_ids: list[str] | None = None,
    ) -> list[str]:
        """为指定关卡选择知识点。

        选择策略：
        1. 优先薄弱知识点（来自记忆层）
        2. 检查前置依赖是否已掌握
        3. 按难度匹配

        Args:
            user_id: 学生用户 ID
            chapter_id: 当前章节 ID
            difficulty_level: 目标难度等级 1-5
            exclude_ids: 需排除的知识点 ID

        Returns:
            选中的知识点 ID 列表
        """
        exclude = set(exclude_ids or [])

        # 基于难度映射知识点数：EASY=1个，ADVANCED=3个
        count = max(1, min(3, difficulty_level // 2 + 1))

        # 从 KG 查询该章节的知识点（Stub: 返回模拟列表）
        candidates = [
            f"kp_{chapter_id}_{i}" for i in range(10)
            if f"kp_{chapter_id}_{i}" not in exclude
        ]

        return candidates[:count]
