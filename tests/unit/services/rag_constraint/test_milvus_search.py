"""Milvus search tests with mock data."""

from __future__ import annotations

import pytest

from src.services.rag_constraint.milvus_search import MilvusSearch


@pytest.fixture
def search() -> MilvusSearch:
    s = MilvusSearch()
    s.add_mock_hit("chunk_1", 0.95, "Fraction comparison tutorial")
    s.add_mock_hit("chunk_2", 0.80, "Common denominator method")
    s.add_mock_hit("chunk_3", 0.60, "Basic addition review")
    return s


class TestMilvusSearch:
    async def test_search_returns_hits(self, search: MilvusSearch) -> None:
        """Should return search results sorted by score."""
        hits = await search.search([0.1] * 1536, top_k=5)
        assert len(hits) == 3
        assert hits[0].score >= hits[1].score

    async def test_top_k_limits(self, search: MilvusSearch) -> None:
        """Should respect top_k limit."""
        hits = await search.search([], top_k=1)
        assert len(hits) == 1

    async def test_search_by_concept(self, search: MilvusSearch) -> None:
        """Should support concept-based search."""
        hits = await search.search_by_concept(["kp_fractions"], top_k=2)
        assert len(hits) <= 2
