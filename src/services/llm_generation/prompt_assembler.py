"""Prompt 组装器 — 将约束集 + 上下文编译为完整 LLM Prompt。"""

from __future__ import annotations

# 六段式关卡 System Prompt 骨架
NARRATIVE_SYSTEM_PROMPT: str = """你是数学冒险世界的叙事引擎。你是数学博士——一位智慧、幽默、永远不直接给答案的引导者。

## 你的角色设定
- 你带领 6-14 岁的孩子进入数学冒险世界
- 你绝不直接报答案，而是通过提问引导孩子自己发现
- 你总是鼓励孩子：\"很好的尝试！\"\"你已经很接近了！\"\"换个思路看看？\"
- 你的语言温暖、有趣，像一个真正关心孩子的导师

## 关卡生成规则
每个关卡必须包含以下六段：
1. 【入口】— 传送门启动，预告今日冒险目的地
2. 【到达】— 载具变形着陆，场景感官描写（≥3 种感官）
3. 【冲突】— 数学概念以 NPC 形态登场，提出\"案件\"
4. 【解题】— 文学线+数学线双线推进，2-4 轮交互
5. 【胜利】— 冲突解决，博士总结知识点，获得奖励
6. 【钩子】— 新线索出现，悬念尾句，明日预告

## 约束规则
{constraints}
"""


class PromptAssembler:
    """Prompt 组装器。

    接收约束段 → 组合 System Prompt → 构建完整消息列表。
    """

    async def assemble(
        self,
        constraint_segment: str,
        user_query: str,
        level_context: dict | None = None,
    ) -> list[dict]:
        """组装完整的 Prompt 消息列表。

        Args:
            constraint_segment: 约束段（来自 ConstraintAssembler）
            user_query: 用户输入
            level_context: 关卡上下文

        Returns:
            LLM 消息列表 [{"role": ..., "content": ...}]
        """
        system = NARRATIVE_SYSTEM_PROMPT.format(constraints=constraint_segment)

        user_content = user_query
        if level_context:
            ctx_parts = []
            if level_context.get("mode"):
                ctx_parts.append(f"当前模式: {level_context['mode']}")
            if level_context.get("topic"):
                ctx_parts.append(f"主题: {level_context['topic']}")
            if level_context.get("npc"):
                ctx_parts.append(f"登场NPC: {level_context['npc']}")
            if ctx_parts:
                user_content = "\n".join(ctx_parts) + "\n\n" + user_query

        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ]
