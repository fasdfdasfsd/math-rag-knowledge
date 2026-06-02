"""Structured logger tests."""

from __future__ import annotations

from unittest.mock import patch

from src.utils.structured_logger import get_logger, setup_logging


class TestGetLogger:
    def test_returns_bound_logger(self) -> None:
        logger = get_logger("test_module")
        # structlog.get_logger 返回 BoundLoggerLazyProxy（延迟绑定）
        assert hasattr(logger, "bind") or hasattr(logger, "info")

    def test_default_name(self) -> None:
        logger = get_logger()
        assert logger is not None


class TestSetupLogging:
    def test_json_format(self) -> None:
        """验证 JSON 格式日志配置不抛异常。"""
        with patch("src.utils.structured_logger.get_settings") as mock_settings:
            mock_settings.return_value = type("Settings", (), {
                "LOG_FORMAT": "json",
                "LOG_LEVEL": "INFO",
            })()
            # 不应抛出异常
            setup_logging()

    def test_console_format(self) -> None:
        """验证控制台格式日志配置不抛异常。"""
        with patch("src.utils.structured_logger.get_settings") as mock_settings:
            mock_settings.return_value = type("Settings", (), {
                "LOG_FORMAT": "console",
                "LOG_LEVEL": "DEBUG",
            })()
            setup_logging()

    def test_default_format(self) -> None:
        """验证默认格式（非 json 即 console）。"""
        with patch("src.utils.structured_logger.get_settings") as mock_settings:
            mock_settings.return_value = type("Settings", (), {
                "LOG_FORMAT": "console",
                "LOG_LEVEL": "WARNING",
            })()
            setup_logging()
