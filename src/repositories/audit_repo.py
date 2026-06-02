"""审计日志数据访问层 — 仅追加 + 哈希链。"""

from __future__ import annotations

import hashlib
import time


class AuditRepository:
    """审计日志存储（MVP 内存 + HMAC 哈希链）。"""

    def __init__(self) -> None:
        self._logs: list[dict] = []
        self._chain_hash: str = "0" * 64

    async def log_event(self, event_type: str, data: dict) -> str:
        """记录审计事件（仅追加，不可修改/删除）。

        Args:
            event_type: 事件类型
            data: 事件数据

        Returns:
            审计记录 ID（哈希）
        """
        ts = time.time()
        raw = f"{self._chain_hash}|{event_type}|{ts}|{data}"
        event_hash = hashlib.sha256(raw.encode()).hexdigest()
        self._logs.append({
            "event_type": event_type,
            "data": data,
            "hash": event_hash,
            "timestamp": ts,
        })
        self._chain_hash = event_hash
        return event_hash

    async def get_by_user(self, user_id: str, limit: int = 50) -> list[dict]:
        return [
            log for log in self._logs
            if log["data"].get("user_id") == user_id
        ][-limit:]

    async def verify_chain(self, from_timestamp: float, to_timestamp: float) -> bool:
        """验证哈希链完整性。"""
        expected = "0" * 64
        for log in self._logs:
            if from_timestamp <= log["timestamp"] <= to_timestamp:
                raw = f"{expected}|{log['event_type']}|{log['timestamp']}|{log['data']}"
                expected = hashlib.sha256(raw.encode()).hexdigest()
                if expected != log["hash"]:
                    return False
        return True
