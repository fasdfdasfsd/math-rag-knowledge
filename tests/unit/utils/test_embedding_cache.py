"""Embedding cache tests."""

from __future__ import annotations

import pytest

from src.utils.embedding_cache import EmbeddingCache


@pytest.fixture
def cache() -> EmbeddingCache:
    return EmbeddingCache()


class TestEmbeddingCache:
    async def test_set_and_get(self, cache: EmbeddingCache) -> None:
        vector = [0.1, 0.2, 0.3]
        await cache.set("hello", vector)
        result = await cache.get("hello")
        assert result == vector

    async def test_miss_returns_none(self, cache: EmbeddingCache) -> None:
        result = await cache.get("nonexistent")
        assert result is None

    async def test_same_text_same_key(self, cache: EmbeddingCache) -> None:
        h1 = cache._hash_key("hello")
        h2 = cache._hash_key("hello")
        assert h1 == h2

    async def test_different_text_different_key(self, cache: EmbeddingCache) -> None:
        h1 = cache._hash_key("hello")
        h2 = cache._hash_key("world")
        assert h1 != h2

    async def test_hit_rate(self, cache: EmbeddingCache) -> None:
        await cache.set("a", [1.0])
        await cache.get("a")  # hit
        await cache.get("b")  # miss
        assert 0.0 < cache.hit_rate < 1.0
