"""Config tests."""

from __future__ import annotations

from src.core.config import Settings, get_settings


class TestSettings:
    def test_defaults(self) -> None:
        s = Settings()
        assert s.APP_NAME != ""
        assert s.JWT_ALGORITHM == "RS256"
        assert s.MILVUS_COLLECTION_PUBLIC == "public_knowledge"
        assert s.MILVUS_COLLECTION_PRIVATE == "private_student_context"

    def test_db_url_format(self) -> None:
        s = Settings(DB_USER="test", DB_PASSWORD="pass", DB_HOST="db", DB_PORT=5432, DB_NAME="math")
        url = s.db_url
        assert url.startswith("postgresql+asyncpg://")
        assert "test:pass@db:5432/math" in url

    def test_redis_url_format(self) -> None:
        s = Settings(REDIS_HOST="rds", REDIS_PORT=6379, REDIS_PASSWORD="pw", REDIS_DB=0)
        assert s.redis_url == "redis://:pw@rds:6379/0"

    def test_get_settings_singleton(self) -> None:
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2
