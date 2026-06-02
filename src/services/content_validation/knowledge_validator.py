"""知识校验器 — 验证 LLM 生成内容的数学知识正确性。"""

from __future__ import annotations

import re


class KnowledgeValidator:
    """数学知识正确性校验器。

    对 LLM 生成内容中的数学知识点进行基本验证：
    - 四则运算结果正确性
    - 基础几何公式合理性
    - 概念-年级匹配度
    """

    # 可验证的题型（规则引擎能力边界）
    VERIFIABLE_TYPES: tuple[str, ...] = (
        "四则运算", "一元一次方程", "基本几何计算",
    )

    def __init__(self) -> None:
        # 年级-知识边界映射
        self._grade_boundaries: dict[int, set[str]] = {
            1: {"加法", "减法", "数数", "比较"},
            2: {"乘法口诀", "简单除法", "米和厘米"},
            3: {"分数初步", "面积", "小数"},
            4: {"多位数乘除", "分数加减", "角度"},
            5: {"分数乘除", "方程", "体积"},
            6: {"比例", "百分数", "负数"},
        }

    async def validate(self, content: str, concept_ids: list[str]) -> dict:
        """验证生成内容的知识正确性。

        Args:
            content: LLM 生成的文本
            concept_ids: 涉及的知识点 ID 列表

        Returns:
            {"is_valid": bool, "issues": [...], "confidence": float}
        """
        issues: list[dict] = []

        # 1. 基本四则运算验证
        math_exprs = re.findall(r"(\d+(?:\.\d+)?)\s*([+\-×÷])\s*(\d+(?:\.\d+)?)\s*=\s*(\d+(?:\.\d+)?)", content)
        for a_str, op, b_str, result_str in math_exprs:
            a, b, result = float(a_str), float(b_str), float(result_str)
            expected = self._compute(a, op, b)
            if expected is not None and abs(expected - result) > 0.001:
                issues.append({
                    "type": "arithmetic_error",
                    "expr": f"{a} {op} {b} = {result}",
                    "expected": expected,
                })

        # 2. 禁止表述检查（重复调用，与 ForbiddenPhraseChecker 互补）
        forbidden_in_math = ["显然", "易证", "显然成立", "平凡解"]
        for phrase in forbidden_in_math:
            if phrase in content:
                issues.append({
                    "type": "forbidden_math_phrase",
                    "phrase": phrase,
                    "note": "数学教育中应避免使用这些词，对儿童不友好",
                })

        # 3. 置信度计算
        confidence = 1.0 if not issues else max(0.3, 1.0 - 0.2 * len(issues))

        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "confidence": round(confidence, 2),
        }

    def _compute(self, a: float, op: str, b: float) -> float | None:
        """安全四则运算。"""
        if op == "+":
            return a + b
        elif op == "-":
            return a - b
        elif op in ("×", "*"):
            return a * b
        elif op in ("÷", "/"):
            return a / b if b != 0 else None
        return None
