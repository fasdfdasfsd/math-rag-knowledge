"""Post-LLM auditor tests."""

from __future__ import annotations

import pytest

from src.services.security.post_llm_auditor import PostLLMAuditor


@pytest.fixture
def auditor() -> PostLLMAuditor:
    return PostLLMAuditor()


class TestAudit:
    async def test_clean_content_approved(self, auditor: PostLLMAuditor) -> None:
        """Clean educational content should pass audit."""
        result = await auditor.audit(
            "小明用通分的方法比较了1/3和1/4的大小。",
            {"user_id": "u1", "level_id": "l1", "user_age": 9},
        )
        assert result["is_approved"] is True
        assert len(result["audit_hash"]) == 64

    async def test_forbidden_phrase_rejected(self, auditor: PostLLMAuditor) -> None:
        """Content with forbidden phrases should be rejected."""
        result = await auditor.audit(
            "正确答案是5，你做错了。",
            {"user_id": "u1", "level_id": "l1", "user_age": 9},
        )
        assert result["is_approved"] is False
        assert len(result["issues"]) > 0

    async def test_violent_content_rejected(self, auditor: PostLLMAuditor) -> None:
        """Violent content should be rejected."""
        result = await auditor.audit(
            "杀死怪物后血流满地。",
            {"user_id": "u1", "level_id": "l1", "user_age": 9},
        )
        assert result["is_approved"] is False

    async def test_hash_chain_grows(self, auditor: PostLLMAuditor) -> None:
        """Audit hash chain should grow with each audit."""
        initial_len = auditor.audit_chain_length
        await auditor.audit("test1", {"user_id": "u1"})
        await auditor.audit("test2", {"user_id": "u1"})
        assert auditor.audit_chain_length == initial_len + 2

    async def test_audit_hashes_unique(self, auditor: PostLLMAuditor) -> None:
        """Each audit should produce a unique hash."""
        r1 = await auditor.audit("content a", {"user_id": "u1"})
        r2 = await auditor.audit("content b", {"user_id": "u1"})
        assert r1["audit_hash"] != r2["audit_hash"]
