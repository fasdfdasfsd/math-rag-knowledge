"""课程一致性校验器 — 确保生成内容与教学大纲对齐。"""

from __future__ import annotations

# 年级→术语白名单（MVP: 小学数学课标关键术语）
GRADE_TERMS: dict[int, set[str]] = {
    1: {"加法", "减法", "数数", "比较", "多少", "大小"},
    2: {"乘法", "除法", "乘法口诀", "厘米", "米", "千克", "克"},
    3: {"分数", "小数", "面积", "周长", "毫米", "千米"},
    4: {"通分", "约分", "角度", "平行", "垂直", "三角形"},
    5: {"方程", "体积", "表面积", "百分数", "比例"},
    6: {"负数", "坐标系", "统计图", "概率"},
}

# 低年级禁止术语
FORBIDDEN_ADVANCED_TERMS: set[str] = {
    "函数", "微积分", "代数", "几何证明", "三角函数",
    "对数", "指数", "复数", "向量", "矩阵",
}


class CurriculumValidator:
    """课程一致性校验器。

    检查 LLM 生成内容是否超纲、难度是否匹配、
    使用的术语是否符合对应年级标准。
    """

    async def validate(self, content: str, grade: int, chapter_id: str) -> dict:
        """校验内容与教学大纲的一致性。

        Args:
            content: LLM 生成的文本
            grade: 目标年级 (1-6)
            chapter_id: 章节 ID

        Returns:
            {"is_aligned": bool, "deviations": [...], "suggestions": [...]}
        """
        deviations: list[dict] = []
        suggestions: list[str] = []

        # 1. 检测超纲术语
        for term in FORBIDDEN_ADVANCED_TERMS:
            if term in content:
                deviations.append({
                    "type": "advanced_term",
                    "term": term,
                    "note": f"{term} 超出小学数学范围",
                })

        # 2. 检查是否使用了符合年级的术语
        allowed = GRADE_TERMS.get(grade, set())
        if allowed:
            # 建议使用年级相关术语（非强约束，仅建议）
            missing_relevant = [t for t in allowed if t not in content]
            if len(missing_relevant) == len(allowed) and len(content) > 50:
                suggestions.append(
                    f"未检测到 {grade} 年级常见术语，建议使用: {', '.join(list(allowed)[:3])}"
                )

        return {
            "is_aligned": len(deviations) == 0,
            "deviations": deviations,
            "suggestions": suggestions,
        }
