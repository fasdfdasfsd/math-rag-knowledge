"""LLM 输出审计器 — Post-LLM 安全检查层。

在 LLM 响应返回给用户前进行多层审计：
- 违禁词检查（调用 ForbiddenPhraseChecker）
- 内容安全审查（调用 ContentSafetyValidator）
- 审计日志记录（不可篡改的哈希链）
"""

from __future__ import annotations

import hashlib
import time

from src.services.content_validation.content_safety_validator import (
    ContentSafetyValidator,
)
from src.services.content_validation.forbidden_phrase_checker import (
    get_forbidden_checker,
)


class PostLLMAuditor:
    """LLM 输出审计器。

    执行 Post-LLM 安全检查流水线：
    违禁词 → 内容安全 → 审计哈希
    """

    def __init__(self) -> None:
        self._phrase_checker = get_forbidden_checker()
        self._safety_validator = ContentSafetyValidator()
        self._audit_chain: list[str] = []  # HMAC 审计链

    async def audit(self, content: str, metadata: dict) -> dict:
        """审计 LLM 输出。

        Args:
            content: LLM 生成的文本
            metadata: 审计元数据（user_id / level_id / model 等）

        Returns:
            {"is_approved": bool, "audit_hash": str, "issues": [...]}
        """
        issues: list[dict] = []

        # 1. 违禁词检查
        phrase_result = await self._phrase_checker.check(content)
        if not phrase_result["is_clean"]:
            issues.append({
                "layer": "forbidden_phrase",
                "matches": phrase_result["matched"],
            })

        # 2. 内容安全审查
        user_age = metadata.get("user_age", 10)
        safety_result = await self._safety_validator.validate(content, user_age)
        if not safety_result.is_safe:
            issues.append({
                "layer": "content_safety",
                "violations": safety_result.violations,
                "replacement": safety_result.replacement_text,
            })

        # 3. 生成审计哈希
        audit_hash = self._chain_hash(content, metadata)

        return {
            "is_approved": len(issues) == 0,
            "audit_hash": audit_hash,
            "issues": issues,
        }

    def _chain_hash(self, content: str, metadata: dict) -> str:
        """链式 HMAC-SHA256 审计哈希（防篡改）。"""
        prev_hash = self._audit_chain[-1] if self._audit_chain else "0" * 64
        data = f"{prev_hash}|{metadata.get('user_id', '')}|{metadata.get('level_id', '')}|{time.time()}|{content[:100]}"
        h = hashlib.sha256(data.encode()).hexdigest()
        self._audit_chain.append(h)
        return h

    @property
    def audit_chain_length(self) -> int:
        """审计链长度。"""
        return len(self._audit_chain)
