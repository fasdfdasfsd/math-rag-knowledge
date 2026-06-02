"""Pregen scheduler tests."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.workers.pregen_scheduler import PregenScheduler


class TestPregenScheduler:
    async def test_start_shutdown(self) -> None:
        s = PregenScheduler()
        await s.start()
        assert s.is_running is True
        await s.shutdown()
        assert s.is_running is False

    async def test_start_without_apscheduler(self) -> None:
        """验证无 APScheduler 时的优雅降级——不崩溃。"""
        with patch("src.workers.pregen_scheduler.HAS_APSCHEDULER", False):
            s = PregenScheduler()
            assert s._scheduler is None
            await s.start()
            assert s.is_running is False

    async def test_shutdown_idempotent(self) -> None:
        """验证对未启动的调度器执行 shutdown 不崩溃。"""
        s = PregenScheduler()
        await s.shutdown()
        assert s.is_running is False

    async def test_init_state(self) -> None:
        s = PregenScheduler()
        assert s.is_running is False

    async def test_start_with_apscheduler(self) -> None:
        """验证有 APScheduler 时的正常启动。"""
        with patch("src.workers.pregen_scheduler.AsyncIOScheduler") as mock_sched:
            mock_instance = MagicMock()
            mock_sched.return_value = mock_instance
            s = PregenScheduler()
            await s.start()
            assert s.is_running is True
            mock_instance.start.assert_called_once()
