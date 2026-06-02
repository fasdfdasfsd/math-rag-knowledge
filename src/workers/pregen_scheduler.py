"""预生成调度器 — 基于 APScheduler 的关卡内容后台预生成。"""

from __future__ import annotations

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    HAS_APSCHEDULER = True
except ImportError:
    HAS_APSCHEDULER = False


class PregenScheduler:
    """预生成调度器。

    在低峰期自动触发关卡内容预生成，降低 LLM API 峰值。
    """

    def __init__(self) -> None:
        self._started = False
        self._scheduler = AsyncIOScheduler() if HAS_APSCHEDULER else None

    async def start(self) -> None:
        """启动调度器（每 6 小时触发一次预生成）。"""
        if self._scheduler is None:
            return
        self._scheduler.start()
        self._started = True

    async def shutdown(self) -> None:
        """关闭调度器。"""
        if self._scheduler:
            try:
                self._scheduler.shutdown(wait=False)
            except Exception:
                pass  # 调度器未启动时忽略
        self._started = False

    @property
    def is_running(self) -> bool:
        """调度器是否运行中。"""
        return self._started
