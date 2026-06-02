"""Milvus client smoke tests."""

from __future__ import annotations

import pytest

from src.core.milvus_client import MilvusClient


class TestMilvusClient:
    def test_initialization(self) -> None:
        client = MilvusClient()
        assert client.is_connected is False

    def test_not_connected_raises(self) -> None:
        client = MilvusClient()
        with pytest.raises(RuntimeError, match="not loaded"):
            _ = client.collection
