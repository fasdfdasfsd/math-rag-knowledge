"""关卡预生成 Worker — 后台批量预生成关卡内容。

MVP 实现：内存队列 + 同步生成，后续接入 LLMProvider + Milvus 缓存。
"""

from __future__ import annotations


class LevelPregenWorker:
    """关卡预生成 Worker。

    在低峰期批量预生成关卡内容，降低 LLM API 峰值压力。
    MVP 使用内存队列，后续接入真实 LLM 生成流水线。
    """

    def __init__(self, pool_size: int = 50, ttl_hours: int = 6) -> None:
        self._pool: dict[str, dict] = {}
        self._pool_size = pool_size
        self._ttl_hours = ttl_hours
        self._stats: dict[str, int] = {"generated": 0, "failed": 0}

    async def pregenerate_levels(
        self, level_ids: list[str], priority: int = 0,
    ) -> dict:
        """预生成指定关卡的内容。

        Args:
            level_ids: 待预生成的关卡 ID 列表
            priority: 优先级（0=普通，1=高，2=紧急）

        Returns:
            预生成结果
        """
        errors: list[str] = []
        generated = 0
        for lid in level_ids:
            if len(self._pool) >= self._pool_size:
                break
            try:
                self._pool[lid] = {
                    "content": f"预生成关卡 {lid} 的内容占位",
                    "created_at": __import__("time").time(),
                    "priority": priority,
                }
                generated += 1
            except Exception as e:
                errors.append(str(e))

        self._stats["generated"] += generated
        self._stats["failed"] += len(errors)

        return {"generated": generated, "failed": len(errors), "errors": errors}

    async def get_predicted_hot_levels(self, limit: int = 50) -> list[str]:
        """获取预测的热门关卡列表（MVP: 返回 pool 中高优先级条目）。"""
        sorted_items = sorted(
            self._pool.items(),
            key=lambda x: (-x[1]["priority"], x[0]),
        )
        return [lid for lid, _ in sorted_items[:limit]]

    def pool_available(self) -> int:
        """池中可用关卡数。"""
        return len(self._pool)

    def pool_capacity_remaining(self) -> int:
        """池剩余容量。"""
        return max(0, self._pool_size - len(self._pool))
