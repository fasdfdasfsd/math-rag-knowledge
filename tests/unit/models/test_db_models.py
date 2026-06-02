"""ORM model smoke tests."""

from __future__ import annotations

import pytest


class TestDBModels:
    def test_user_model_import(self) -> None:
        from src.models.db.user import User, UserProgress, ParentChildRelation
        assert User.__tablename__ == "users"
        assert ParentChildRelation.__tablename__ == "parent_child_relations"

    def test_knowledge_model_import(self) -> None:
        from src.models.db.knowledge import KnowledgeConcept, KnowledgeRelation
        assert KnowledgeConcept.__tablename__ is not None

    def test_adventure_model_import(self) -> None:
        from src.models.db.adventure import World, Chapter, Level
        assert World.__tablename__ is not None

    def test_npc_model_import(self) -> None:
        from src.models.db.npc import NPC, NPCDialogue
        assert NPC.__tablename__ is not None

    def test_memory_model_import(self) -> None:
        from src.models.db.memory import StudentMemory
        assert StudentMemory.__tablename__ is not None

    def test_security_model_import(self) -> None:
        from src.models.db.security import AuditLog, ContentReport
        assert AuditLog.__tablename__ is not None
