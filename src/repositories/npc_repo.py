"""NPC 数据访问层。"""

from __future__ import annotations


class NPCRepository:
    """NPC 数据操作（MVP 内存存储）。"""

    def __init__(self) -> None:
        self._npcs: dict[str, dict] = {}
        self._dialogues: dict[str, list[dict]] = {}

    async def get_by_id(self, npc_id: str) -> dict | None:
        return self._npcs.get(npc_id)

    async def get_by_level(self, level_id: str) -> list[dict]:
        return [n for n in self._npcs.values() if level_id in n.get("level_ids", [])]

    async def create_npc(self, data: dict) -> dict:
        nid = data.get("id", f"npc_{len(self._npcs)+1}")
        data["id"] = nid
        self._npcs[nid] = data
        return data

    async def update_dialogue(self, npc_id: str, dialogue_data: dict) -> dict:
        if npc_id not in self._dialogues:
            self._dialogues[npc_id] = []
        self._dialogues[npc_id].append(dialogue_data)
        return dialogue_data
