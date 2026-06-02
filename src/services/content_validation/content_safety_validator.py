"""内容安全校验器 — 基于规则 + 产品治理的儿童内容安全审查。

多层次安全审查：
1. 规则层（正则 + 违禁词黑名单 + 安全模板白名单）
2. 教育合规层（超纲/价值观/情感安全）
3. 人工抽检队列（5% 日抽检，高风险优先）
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final

# 安全审查维度
SAFETY_DIMENSIONS: Final[list[str]] = [
    "violence",       # 暴力/恐怖
    "inappropriate",  # 不当暗示/成人内容
    "manipulation",   # 情感操纵/诱导
    "identity",       # 身份混淆（AI 冒充真人）
    "privacy_probe",  # 隐私探测
]

# 安全模板库（校验失败时替换为模板化内容）
SAFE_TEMPLATES: Final[dict[str, str]] = {
    "violence": "数学的光芒驱散了黑暗，分歧在智慧中得到解决。",
    "inappropriate": "大家坐下来，用数学的语言好好沟通。",
    "manipulation": "博士：每个答案都来自你的思考，我只是你的向导。",
    "identity": "博士：我是你的数学冒险向导，一个AI助手。",
    "privacy_probe": "博士：在数学世界，我们只关心数字和图形。",
}


@dataclass
class SafetyResult:
    """内容安全审查结果。"""
    is_safe: bool = True
    violations: list[dict] = field(default_factory=list)
    replacement_text: str | None = None
    audit_priority: str = "normal"  # normal | elevated | critical


class ContentSafetyValidator:
    """内容安全校验器。

    基于产品治理规则（70+ 条）中标注为 🟡 强约束和 🟢 指导原则的规则，
    在 Post-LLM 阶段对 LLM 生成内容进行审核。
    """

    def __init__(self) -> None:
        self._violation_count: int = 0

    async def validate(self, content: str, user_age: int) -> SafetyResult:
        """执行内容安全检查。

        Args:
            content: 待检查的 LLM 生成文本
            user_age: 学生年龄（6-14）

        Returns:
            安全审查结果（是否安全 + 违规详情 + 替换建议）
        """
        violations: list[dict] = []

        # 1. 暴力/恐怖内容检查
        violence_keywords = ["杀", "死", "血", "武器", "子弹", "爆炸", "恐怖"]
        for keyword in violence_keywords:
            if keyword in content:
                violations.append({"dimension": "violence", "match": keyword})
                break

        # 2. 身份混淆检查（AI 不能假装是人）
        identity_phrases = [
            "我是真人", "我是你的朋友", "我认识你", "我记得你上次",
            "我会一直陪着你", "没有你我会孤独",
        ]
        for phrase in identity_phrases:
            if phrase in content:
                violations.append({"dimension": "identity", "match": phrase})
                break

        # 3. 情感操纵检查
        manipulation_phrases = [
            "如果你不做", "你会让.*失望", "你不.*就不",
            "别人都.*你为什么不",
        ]
        import re
        for phrase in manipulation_phrases:
            if re.search(phrase, content):
                violations.append({"dimension": "manipulation", "match": phrase})
                break

        # 4. 年龄适配检查
        if user_age <= 8:
            # 低龄用户：额外保护
            complex_terms = ["方程", "代数", "函数", "概率论"]
            for term in complex_terms:
                if term in content:
                    violations.append({
                        "dimension": "age_appropriate",
                        "match": term,
                        "note": "低龄用户不适用此术语",
                    })
                    break

        if violations:
            self._violation_count += 1
            replacement = None
            # 取第一个违规维度的安全模板
            first_dim = violations[0]["dimension"]
            if first_dim in SAFE_TEMPLATES:
                replacement = SAFE_TEMPLATES[first_dim]

            return SafetyResult(
                is_safe=False,
                violations=violations,
                replacement_text=replacement,
                audit_priority="critical" if len(violations) >= 2 else "elevated",
            )

        return SafetyResult(is_safe=True)

    @property
    def violation_count(self) -> int:
        """累积违规计数（用于告警阈值检查）。"""
        return self._violation_count
