"""
日志配置模块
-------------
提供统一的日志记录器，包含时间戳、模块名和级别。
所有模块通过 setup_logger(__name__) 获取 logger 实例。
"""
import logging


def setup_logger(name: str) -> logging.Logger:
    """
    创建并配置一个标准日志记录器。
    :param name: 日志记录器名称（建议使用 __name__）
    :return: 配置好的 Logger 实例
    """
    logger = logging.getLogger(name)
    if not logger.handlers:  # 避免重复添加处理器
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger