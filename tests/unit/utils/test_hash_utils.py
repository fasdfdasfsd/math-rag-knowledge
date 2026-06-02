"""Hash utils tests."""

from __future__ import annotations

from src.utils.hash_utils import content_checksum, audit_hash


def test_content_checksum_deterministic() -> None:
    """Same input produces same hash."""
    h1 = content_checksum("hello world")
    h2 = content_checksum("hello world")
    assert h1 == h2

def test_content_checksum_different() -> None:
    """Different inputs produce different hashes."""
    h1 = content_checksum("hello")
    h2 = content_checksum("world")
    assert h1 != h2

def test_audit_hash_chain() -> None:
    """Audit hash produces different values for different inputs."""
    h1 = audit_hash("event_data_1", "prev_hash_1")
    h2 = audit_hash("event_data_2", "prev_hash_2")
    assert h1 != h2
