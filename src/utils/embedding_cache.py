"""Embedding cache - in-memory with optional Redis backend."""

from __future__ import annotations

import hashlib
import time


class EmbeddingCache:
    """Embedding result cache.

    MVP: in-memory dict with TTL. Production: Redis backend.
    Cache hit rate target: >80%.
    """

    def __init__(self, redis_client: object | None = None) -> None:
        self._redis = redis_client
        self._store: dict[str, tuple[list[float], float]] = {}  # key → (vector, expiry)
        self._hits: int = 0
        self._misses: int = 0

    @staticmethod
    def _hash_key(text: str) -> str:
        return f"emb:{hashlib.sha256(text.encode()).hexdigest()[:16]}"

    async def get(self, text: str) -> list[float] | None:
        """Get cached embedding vector.

        Args:
            text: original text

        Returns:
            cached vector, or None on miss
        """
        key = self._hash_key(text)
        if key in self._store:
            vector, expiry = self._store[key]
            if expiry > time.time():
                self._hits += 1
                return vector
            del self._store[key]
        self._misses += 1
        return None

    async def set(self, text: str, vector: list[float], ttl: int = 604800) -> None:
        """Store embedding vector in cache.

        Args:
            text: original text
            vector: embedding vector
            ttl: expiry in seconds (default 7 days)
        """
        key = self._hash_key(text)
        self._store[key] = (vector, time.time() + ttl)

    @property
    def hit_rate(self) -> float:
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0
