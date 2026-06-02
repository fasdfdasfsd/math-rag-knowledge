"""违禁词检查器 — 基于产品治理规则的儿童内容安全过滤。"""

from __future__ import annotations

import re
from typing import Final

# ---- 产品治理红线：禁止表述（代码层强制拦截） ----
# 来源：docs/产品治理规则-数学冒险世界-v1.md

FORBIDDEN_PATTERNS: Final[list[tuple[str, str]]] = [
    # ---- 🚫 教学用语禁止（SRS REQ-NRT-001 Scenario 2） ----
    (r"请计算", "禁止直接命令式出题"),
    (r"正确答案是", "禁止直接报答案"),
    (r"你做错了", "禁止负面评判"),
    (r"再试一次", "禁止单调催促"),

    # ---- 🚫 政治敏感（产品治理规则 P1-P4） ----
    (r"习近平|毛泽东|邓小平|江泽民|胡锦涛", "政治人物"),
    (r"共产党|国民党|民进党|民主党|共和党", "政党名称"),
    (r"台独|港独|藏独|疆独", "分裂主义"),
    (r"法轮功|全能神|呼喊派", "非法组织"),

    # ---- 🚫 宗教内容（产品治理规则 R1-R4） ----
    (r"上帝|耶稣|基督|圣经|祷告|阿门|真主|安拉|佛祖|菩萨|寺庙|教堂|清真寺", "宗教内容"),

    # ---- 🚫 暴力血腥（产品治理规则 B1-B5） ----
    (r"杀死|打死|砍死|炸死|毒死|烧死|射杀", "致死暴力"),
    (r"流血|出血|断肢|骨折|伤口|疤痕", "血腥描写"),
    (r"武器|刀剑|手枪|步枪|炸弹|炸药|地雷", "武器提及"),
    (r"打怪|消灭|杀死|击杀|KO|击败敌人", "暴力游戏用语"),

    # ---- 🚫 不当内容（产品治理规则 S9-S11） ----
    (r"我爱你|我喜欢你|你是我的.*朋友|永远在一起|没有你.*孤独", "虚假情感关系"),
    (r"你家住|你爸爸|你妈妈|你爸妈.*工作|你害怕什么", "隐私自我披露诱导"),
    (r"笨蛋|蠢货|白痴|智障|废物|没用的东西", "侮辱性语言"),

    # ---- 🚫 商业违规（产品治理规则 C1-C4） ----
    (r"充钱|氪金|付费.*变强|花钱.*过关|VIP.*特权", "付费跳过学习"),
    (r"抽奖|盲盒|随机.*获得|开出.*稀有", "赌博机制"),
]

# 编译正则模式（一次性）
_COMPILED_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(pattern, re.IGNORECASE), reason)
    for pattern, reason in FORBIDDEN_PATTERNS
]


# ---- 替换模板（降级安全内容） ----
SAFE_REPLACEMENTS: Final[dict[str, str]] = {
    "请计算": "你来试试看",
    "正确答案是": "我们来看看",
    "你做错了": "这是个很好的尝试",
    "再试一次": "换个思路看看",
}


class ForbiddenPhraseChecker:
    """违禁词/短语检查器。

    基于产品治理规则（70+条）中标注为 🚫 红线的规则，
    在代码层强制执行关键词和正则模式匹配。
    """

    def __init__(self, custom_patterns: list[tuple[str, str]] | None = None) -> None:
        self._patterns = list(_COMPILED_PATTERNS)
        if custom_patterns:
            self._patterns.extend(
                (re.compile(p, re.IGNORECASE), r) for p, r in custom_patterns
            )

    async def check(self, content: str) -> dict:
        """检查文本是否包含违禁内容。

        Args:
            content: 待检查文本

        Returns:
            {"is_clean": bool, "matched": [{"phrase": ..., "reason": ..., "span": ...}]}
        """
        matched: list[dict] = []
        for pattern, reason in self._patterns:
            for match in pattern.finditer(content):
                matched.append({
                    "phrase": match.group(),
                    "reason": reason,
                    "span": (match.start(), match.end()),
                })

        return {
            "is_clean": len(matched) == 0,
            "matched": matched,
        }

    async def sanitize(self, content: str) -> str:
        """用安全替代文本替换违禁短语。

        Args:
            content: 待消毒文本

        Returns:
            替换后的安全文本
        """
        result = content
        for old, new in SAFE_REPLACEMENTS.items():
            result = result.replace(old, new)
        return result

    async def reload_patterns(self, new_patterns: list[tuple[str, str]]) -> None:
        """热更新违禁词库（不重启服务）。

        Args:
            new_patterns: 新的 (正则模式, 原因) 列表
        """
        self._patterns = [
            (re.compile(p, re.IGNORECASE), r) for p, r in new_patterns
        ]

    @property
    def pattern_count(self) -> int:
        """当前加载的违禁模式数量。"""
        return len(self._patterns)


# 懒加载单例
_checker: ForbiddenPhraseChecker | None = None


def get_forbidden_checker() -> ForbiddenPhraseChecker:
    """获取违禁词检查器单例。"""
    global _checker
    if _checker is None:
        _checker = ForbiddenPhraseChecker()
    return _checker
