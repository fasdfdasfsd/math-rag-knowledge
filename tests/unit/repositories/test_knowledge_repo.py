"""Knowledge repository tests."""

from __future__ import annotations

import pytest

from src.repositories.knowledge_repo import KnowledgeRepository


@pytest.fixture
def repo() -> KnowledgeRepository:
    r = KnowledgeRepository()
    r._concepts = {
        "kp_add": {"id": "kp_add", "name": "Addition", "grade": 1},
        "kp_mult": {"id": "kp_mult", "name": "Multiplication", "grade": 2},
        "kp_frac": {"id": "kp_frac", "name": "Fractions", "grade": 3},
    }
    r._relations = [
        {"source": "kp_add", "target": "kp_mult", "type": "prerequisite"},
        {"source": "kp_mult", "target": "kp_frac", "type": "prerequisite"},
        {"source": "kp_frac", "target": "kp_dec", "type": "related"},
    ]
    return r


class TestKnowledgeRepo:
    async def test_get_concept(self, repo: KnowledgeRepository) -> None:
        c = await repo.get_concept_by_id("kp_add")
        assert c is not None
        assert c["name"] == "Addition"

    async def test_get_prerequisites(self, repo: KnowledgeRepository) -> None:
        prereqs = await repo.get_prerequisites("kp_mult")
        assert "kp_add" in prereqs

    async def test_list_by_grade(self, repo: KnowledgeRepository) -> None:
        concepts = await repo.list_concepts(grade=1)
        assert len(concepts) == 1

    async def test_get_related(self, repo: KnowledgeRepository) -> None:
        related = await repo.get_related_concepts(["kp_frac"])
        assert "kp_dec" in related

    async def test_upsert_concept(self, repo: KnowledgeRepository) -> None:
        await repo.upsert_concept({"id": "kp_new", "name": "Geometry", "grade": 4})
        c = await repo.get_concept_by_id("kp_new")
        assert c is not None
