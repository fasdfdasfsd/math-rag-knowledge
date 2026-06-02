"""哈希工具 — 内容排重哈希 + 审计日志哈希链。"""

from __future__ import annotations

import hashlib


def content_checksum(content: str) -> str:
    """计算内容排重哈希（SHA-256 前 16 字符）。

    用于关卡内容缓存的排重检测。

    Args:
        content: 文本内容

    Returns:
        16 字符的十六进制哈希
    """
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def audit_hash(
    event_data: str,
    previous_hash: str | None = None,
) -> str:
    """计算审计日志哈希（SHA-256）。

    审计哈希链公式：
        current_hash = SHA-256(previous_hash + "|" + event_data)

    Args:
        event_data: 事件数据的 JSON 序列化字符串
        previous_hash: 前一条审计记录的哈希值

    Returns:
        64 字符的十六进制哈希
    """
    raw = event_data
    if previous_hash:
        raw = f"{previous_hash}|{event_data}"
    return hashlib.sha256(raw.encode()).hexdigest()
