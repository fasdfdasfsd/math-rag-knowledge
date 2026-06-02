"""审计日志仓库测试。"""

from __future__ import annotations

import pytest

from src.repositories.audit_repo import AuditRepository


@pytest.fixture
def repo() -> AuditRepository:
    return AuditRepository()


class TestLogEvent:
    async def test_log_returns_hash(self, repo: AuditRepository) -> None:
        """应返回 64 字符哈希。"""
        h = await repo.log_event("test", {"user_id": "u1", "action": "login"})
        assert len(h) == 64

    async def test_chain_integrity(self, repo: AuditRepository) -> None:
        """哈希链应可验证。"""
        h1 = await repo.log_event("e1", {"user_id": "u1"})
        h2 = await repo.log_event("e2", {"user_id": "u1"})
        assert h1 != h2
        # 使用足够大的时间窗口确保覆盖
        t = __import__("time").time()
        assert await repo.verify_chain(0, t + 10)


class TestGetByUser:
    async def test_filters_by_user(self, repo: AuditRepository) -> None:
        """应按 user_id 过滤。"""
        await repo.log_event("login", {"user_id": "u1"})
        await repo.log_event("play", {"user_id": "u2"})
        await repo.log_event("play", {"user_id": "u1"})
        logs = await repo.get_by_user("u1", limit=10)
        assert len(logs) == 2
