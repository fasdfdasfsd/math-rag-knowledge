"""Memory assembler tests."""

from __future__ import annotations

import pytest

from src.services.rag_constraint.memory_assembler import MemoryAssembler


@pytest.fixture
def mem() -> MemoryAssembler:
    return MemoryAssembler()


class TestAssembleMemory:
    async def test_empty_memory(self, mem: MemoryAssembler) -> None:
        """New user returns empty memory."""
        result = await mem.assemble_memory("new_user")
        assert result["recent_mistakes"] == []
        assert result["mastered_concepts"] == []
        assert result["last_session_summary"] is None

    async def test_assemble_returns_data(self, mem: MemoryAssembler) -> None:
        """Updated memory returns stored data."""
        await mem.update_memory("u1", "s1", {
            "correct": ["addition"], "incorrect": ["multiplication"],
            "summary": "Learned fractions today",
        })
        result = await mem.assemble_memory("u1")
        assert "addition" in result["mastered_concepts"]
        assert "multiplication" in result["struggling_concepts"]
        assert result["last_session_summary"] == "Learned fractions today"


class TestUpdateMemory:
    async def test_correct_removes_from_struggling(self, mem: MemoryAssembler) -> None:
        """Mastering removes from struggling list."""
        await mem.update_memory("u1", "s1", {"incorrect": ["fractions"]})
        await mem.update_memory("u1", "s2", {"correct": ["fractions"]})
        result = await mem.assemble_memory("u1")
        assert "fractions" not in result["struggling_concepts"]

    async def test_mistakes_limited_to_50(self, mem: MemoryAssembler) -> None:
        """Mistake list capped at 50 items."""
        for i in range(60):
            await mem.update_memory("u1", f"s{i}", {"incorrect": [f"kp_{i}"]})
        result = await mem.assemble_memory("u1")
        assert len(result["recent_mistakes"]) <= 50
