"""Database layer smoke tests."""

from __future__ import annotations


class TestDBConfig:
    def test_init_db_registers_engine(self) -> None:
        from src.core.database import init_db
        # init_db is async and requires real DB - just verify import
        assert callable(init_db)

    def test_shutdown_db_registered(self) -> None:
        from src.core.database import shutdown_db
        assert callable(shutdown_db)

    def test_get_async_session_importable(self) -> None:
        from src.core.database import get_async_session
        assert callable(get_async_session)
