"""应用配置 — 环境变量驱动，Pydantic Settings 管理。"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用全局配置。

    优先级：环境变量 > .env 文件 > 默认值。
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ---- 应用基础 ----
    APP_NAME: str = "数学冒险世界"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"  # development | staging | production

    # ---- PostgreSQL ----
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "mathrag"
    DB_PASSWORD: str = "mathrag_dev"
    DB_NAME: str = "math_rag"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_ECHO: bool = False

    @property
    def db_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    # ---- Milvus ----
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_ALIAS: str = "default"
    MILVUS_COLLECTION_PUBLIC: str = "public_knowledge"
    MILVUS_COLLECTION_PRIVATE: str = "private_student_context"
    MILVUS_EMBEDDING_DIM: int = 1536  # DeepSeek Embedding 输出维度

    # ---- Redis ----
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = "mathrag_dev"
    REDIS_DB: int = 0
    REDIS_MAXMEMORY: str = "2gb"

    @property
    def redis_url(self) -> str:
        return (
            f"redis://:{self.REDIS_PASSWORD}"
            f"@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        )

    # ---- LLM ----
    LLM_PROVIDER: str = "deepseek"  # deepseek | tongyi
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"
    TONGYI_API_KEY: str = ""
    TONGYI_MODEL: str = "qwen-plus"
    LLM_TIMEOUT_SECONDS: int = 60  # LLM 生成超时
    LLM_MAX_RETRIES: int = 1  # 重生成限制（P95<60s 约束）

    # ---- JWT（RS256 非对称 — 安全红线）----
    JWT_PRIVATE_KEY: str = ""  # RS256 私钥（PEM 格式 或文件路径）
    JWT_PUBLIC_KEY: str = ""  # RS256 公钥
    JWT_ALGORITHM: str = "RS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ---- 安全 ----
    MAX_INPUT_LENGTH: int = 4000
    RATE_LIMIT_PER_MINUTE: int = 60
    CONTENT_CACHE_TTL_HOURS: int = 72
    PII_MASK_PATTERNS: list[str] = [
        r"\b\d{11}\b",  # 手机号
        r"\b\d{17}[\dXx]\b",  # 身份证
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",  # 邮箱
    ]

    # ---- 内容校验 ----
    VALIDATION_SERVICE_URL: str = "http://localhost:8010"
    DAILY_SAMPLE_RATE: float = 0.05  # 5% 人工抽检
    MATH_CORRECTNESS_ALERT_THRESHOLD: float = 0.95  # 正确率低于 95%→告警

    # ---- 预生成池 ----
    PREGEN_POOL_SIZE: int = 50  # 预生成池目标大小
    PREGEN_TTL_HOURS: int = 6  # 预生成关卡过期时间
    PREGEN_LOW_WATERMARK: int = 20  # 低水位 → 紧急补充
    PREGEN_HIGH_WATERMARK: int = 80  # 高水位 → 暂停生成

    # ---- 日志 ----
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json | console

    # ---- PWA Push Notification (VAPID) ----
    VAPID_PRIVATE_KEY: str = ""
    VAPID_PUBLIC_KEY: str = ""
    VAPID_CLAIM_EMAIL: str = "admin@math-adventure.local"
    PUSH_SUBSCRIPTION_TTL_HOURS: int = 72


@lru_cache
def get_settings() -> Settings:
    """获取单例配置（带缓存）。"""
    return Settings()
