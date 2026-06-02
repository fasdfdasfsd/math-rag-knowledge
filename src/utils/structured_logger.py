"""结构化日志配置 — 基于 structlog，JSON 格式输出。"""

from __future__ import annotations

import logging
import sys

import structlog

from src.core.config import get_settings


def setup_logging() -> None:
    """初始化 structlog 配置。

    输出格式：
    - JSON 格式（生产环境，默认）
    - 控制台彩色格式（DEBUG 模式）
    - 所有日志包含 timestamp / level / logger 字段
    """
    settings = get_settings()

    shared_processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if settings.LOG_FORMAT == "json":
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    handler = logging.StreamHandler(sys.stdout)
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(settings.LOG_LEVEL)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """获取结构化日志器。"""
    return structlog.get_logger(name or __name__)
