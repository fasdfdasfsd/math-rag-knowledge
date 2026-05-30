---
category: 07-数据库规范
priority: must
updated: 2026-05-30
---

# PostgreSQL 规范

## 概述

本文档定义 PostgreSQL 数据库的设计与使用规范，涵盖表设计范式、主键策略（UUID vs SERIAL）、索引策略（复合索引、部分索引、覆盖索引）、查询优化方法（EXPLAIN ANALYZE、慢查询定位）、pgvector 扩展使用以及连接池配置（asyncpg）。适用于所有使用 PostgreSQL 作为主数据库的项目。

## 核心规则

### MUST（强制遵守）

#### 表设计

- 所有表必须包含主键。推荐使用 UUID v4 作为主键（分布式友好、安全、无自增冲突），或在明确只需要单机时序场景时使用 `IDENTITY`（PostgreSQL 10+ 替代 `SERIAL`）。
- 表名使用复数 snake_case（`users`, `orders`, `order_items`）。
- 所有表必须包含审计字段：

```sql
CREATE TABLE users (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email       VARCHAR(255) NOT NULL,
    display_name VARCHAR(100),
    status      VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at  TIMESTAMPTZ       -- 软删除标记（如果业务需要）
);

-- 自动更新 updated_at 触发器
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

- 字段类型选择：
  - 整数：`INTEGER` / `BIGINT`，避免 `SMALLINT` / `INT2`。
  - 浮点数：`NUMERIC(precision, scale)` 用于精确计算（金额），`DOUBLE PRECISION` 用于近似计算。
  - 文本：`VARCHAR(n)` 或 `TEXT`（长度无差异）。
  - 时间：`TIMESTAMPTZ`（始终带时区），避免 `TIMESTAMP` 和 `DATE` 的时间处理歧义。
  - JSON：使用 `JSONB` 而非 `JSON`（支持索引和高效操作）。
  - 布尔值：`BOOLEAN`，勿用 `CHAR(1)` 替代。

#### 索引策略

- 为所有 `WHERE` / `JOIN` / `ORDER BY` 中高频使用的列创建索引。
- 复合索引：列顺序遵循「等值条件列优先，范围条件列次之」原则。

```sql
-- 查询模式：WHERE status = 'active' AND created_at > '2024-01-01'
-- 正确索引顺序
CREATE INDEX idx_users_status_created_at ON users (status, created_at);
-- 解释：先 status（等值过滤），后 created_at（范围过滤）

-- 错误索引顺序
CREATE INDEX idx_users_created_at_status ON users (created_at, status);
-- B-Tree 首先按 created_at 排序，等值过滤 status 无法高效定位
```

- 部分索引（Partial Index）：过滤高频查询条件，大幅节省空间。

```sql
-- 只有 active 用户被高频查询
CREATE INDEX idx_users_active_email ON users (email)
    WHERE status = 'active';
```

- 覆盖索引（Covering Index）：包含所有查询列的索引，避免回表。

```sql
-- 查询只涉及 user_id 和 status
CREATE INDEX idx_orders_user_status_covering ON orders (user_id, status)
    INCLUDE (total_amount, created_at);
```

- 禁止在低选择性的列上建索引（如性别 `male` / `female` 二值列）。
- 索引命名规范：`idx_表名_列名`，唯一索引：`uidx_表名_列名`。

#### 查询优化

- 所有关键查询必须经过 `EXPLAIN ANALYZE` 评估执行计划。
- 关注指标：
  - `Seq Scan` – 表扫描，通常表示缺少索引。
  - `Index Scan` / `Index Only Scan` – 理想。
  - `Rows Removed by Filter` – 过滤了大量行，可能需要调整索引。
  - `Buffers: shared hit/read` – 缓冲区命中率应 >99%。
- 慢查询标准：执行时间超过 200ms 为「慢查询」，必须优化。

```sql
EXPLAIN (ANALYZE, BUFFERS, TIMING)
SELECT u.id, u.email, o.total_amount
FROM users u
INNER JOIN orders o ON o.user_id = u.id
WHERE u.status = 'active'
  AND o.created_at >= '2024-06-01'
ORDER BY o.created_at DESC
LIMIT 20;
```

#### 连接池配置

- 禁止在请求处理中直接创建新数据库连接。必须使用连接池。
- asyncpg 连接池推荐配置：

```python
import asyncpg
from typing import AsyncIterator
from contextlib import asynccontextmanager


class DatabasePoolManager:
    """PostgreSQL connection pool manager using asyncpg."""

    def __init__(
        self,
        dsn: str,
        min_size: int = 10,
        max_size: int = 50,
        max_queries: int = 50000,
        max_inactive_connection_lifetime: float = 300.0,
    ):
        self.dsn = dsn
        self.min_size = min_size
        self.max_size = max_size
        self.max_queries = max_queries
        self.max_inactive_connection_lifetime = max_inactive_connection_lifetime
        self._pool: asyncpg.Pool | None = None

    async def init(self) -> None:
        """Initialize the connection pool."""
        self._pool = await asyncpg.create_pool(
            dsn=self.dsn,
            min_size=self.min_size,
            max_size=self.max_size,
            max_queries=self.max_queries,
            max_inactive_connection_lifetime=self.max_inactive_connection_lifetime,
            command_timeout=30,
            statement_cache_size=0,
        )

    async def close(self) -> None:
        """Close all connections in the pool."""
        if self._pool:
            await self._pool.close()

    @asynccontextmanager
    async def acquire(self) -> AsyncIterator[asyncpg.Connection]:
        """Acquire a connection from the pool."""
        if self._pool is None:
            raise RuntimeError("Pool not initialized")
        async with self._pool.acquire() as conn:
            yield conn


# 使用示例
db = DatabasePoolManager(dsn="postgresql://user:pass@localhost:5432/myapp")
await db.init()
async with db.acquire() as conn:
    result = await conn.fetch("SELECT id, email FROM users WHERE status = $1", "active")
```

### SHOULD（建议遵守）

#### 约束与验证

- 使用 `CHECK` 约束验证字段值的合法性（如状态枚举）。
- 使用 `NOT NULL` 约束明确排除空值，允许空值则不加限制。
- 唯一约束使用 `UNIQUE` 或唯一索引。

```sql
CREATE TABLE orders (
    id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status   VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'paid', 'shipped', 'cancelled')),
    email    VARCHAR(255),
    CONSTRAINT uq_orders_external_id UNIQUE (external_id)
);
```

#### 分区表

- 大表（预期 > 1000 万行）应使用表分区。
- 按时间分区是最常见的策略（`RANGE PARTITION BY created_at`）。

```sql
CREATE TABLE events (
    id         UUID NOT NULL DEFAULT gen_random_uuid(),
    event_type VARCHAR(50) NOT NULL,
    payload    JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (created_at);

CREATE TABLE events_2024_q1 PARTITION OF events
    FOR VALUES FROM ('2024-01-01') TO ('2024-04-01');

CREATE TABLE events_2024_q2 PARTITION OF events
    FOR VALUES FROM ('2024-04-01') TO ('2024-07-01');
```

#### 迁移管理

- 使用版本化迁移工具（Alembic 或 Flyway）。
- 迁移文件名格式：`{版本号}_{描述}.sql`（如 `20240530_add_user_status_index.sql`）。
- 生产环境 DDL 操作需审核，大表变更（如添加列默认值）使用多步骤策略。

### MAY（可选的推荐）

- 大 JSONB 字段单独拆表，按需 JOIN 加载。
- 计数器字段存储在 Redis 而非 PostgreSQL（避免行锁争用）。
- 归档策略：定期将历史数据迁移到归档表或 ClickHouse。

## 正确示例

```python
# 完整查询优化示例
import asyncpg
from datetime import datetime, timedelta


async def get_active_users_with_recent_orders(
    pool: asyncpg.Pool,
    days: int = 30,
    limit: int = 20,
    offset: int = 0,
) -> list[dict]:
    """Fetch active users with orders in the last N days.

    Uses a join with a derived table to avoid N+1 queries.
    """
    query = """
        SELECT
            u.id,
            u.email,
            u.display_name,
            o.id        AS last_order_id,
            o.total_amount,
            o.created_at AS last_order_date
        FROM users u
        INNER JOIN LATERAL (
            SELECT id, total_amount, created_at
            FROM orders
            WHERE user_id = u.id
              AND status IN ('paid', 'shipped')
            ORDER BY created_at DESC
            LIMIT 1
        ) o ON TRUE
        WHERE u.status = 'active'
          AND EXISTS (
            SELECT 1
            FROM orders
            WHERE user_id = u.id
              AND created_at >= NOW() - $1::INTERVAL
          )
        ORDER BY o.created_at DESC
        LIMIT $2 OFFSET $3
    """
    rows = await pool.fetch(query, timedelta(days=days), limit, offset)
    return [dict(row) for row in rows]
```

```sql
-- 正确的索引设计（匹配查询模式）
-- 查询 A: WHERE status = 'active' AND created_at >= DATE '2024-01-01'
CREATE INDEX idx_users_status_created_at ON users (status, created_at);

-- 查询 B: WHERE email ILIKE 'example%'
CREATE INDEX idx_users_email_trgm ON users USING gin (email gin_trgm_ops);

-- 查询 C: WHERE metadata @> '{"country": "CN"}'
CREATE INDEX idx_users_metadata ON users USING gin (metadata jsonb_path_ops);
```

## 错误示例

```sql
-- 错误 1：缺少主键
CREATE TABLE users (
    email VARCHAR(255) NOT NULL
);
-- 缺少主键导致：
--   - 无法有效 UNIQUE 约束（需额外索引）
--   - 复制/逻辑解码困难
--   - ORM 对接问题

-- 错误 2：使用 SERIAL 而非 UUID（分布式场景）
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    ...
);
-- 自增 ID 在分布式环境、多服务或数据合并场景会产生冲突

-- 错误 3：索引列顺序错误
CREATE INDEX idx_users_status_created_at ON users (created_at, status);
-- 对于 WHERE status = 'active' AND created_at > '2024-01-01' 查询，
-- status 等值过滤在前更高效

-- 错误 4：在全表扫描基础上建索引
-- 表只有 3 条数据时不需要索引，全表扫描更快

-- 错误 5：LIKE 查询未使用 trigram 索引
SELECT * FROM users WHERE email LIKE '%example%';
-- 应使用 GIN trigram 索引

-- 错误 6：没有连接池，每个请求创建新连接
async def get_user(user_id: str):
    conn = await asyncpg.connect(DATABASE_URL)  -- 每次请求新建连接
    try:
        row = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
        return dict(row) if row else None
    finally:
        await conn.close()

-- 错误 7：事务内执行长时间操作
BEGIN;
SELECT ... FROM users WHERE id = $1;    -- 占用连接
-- 调用外部 API（2 秒）
-- ...
COMMIT;

-- 错误 8：没有审计字段
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    total_amount NUMERIC(10, 2) NOT NULL
    -- 缺少 created_at, updated_at
);
```

## 工具链配置

### pgvector 扩展配置

```sql
-- 启用扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- 创建向量表
CREATE TABLE document_embeddings (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    chunk_text  TEXT NOT NULL,
    embedding   VECTOR(1536) NOT NULL,        -- OpenAI text-embedding-3-small 维度
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- HNSW 索引（推荐，精度更高）
CREATE INDEX idx_doc_embeddings_hnsw
    ON document_embeddings
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 200);

-- IVFFlat 索引（构建快，适合大规模数据集）
CREATE INDEX idx_doc_embeddings_ivfflat
    ON document_embeddings
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
```

### PostgreSQL 配置优化

```ini
# postgresql.conf 关键参数
max_connections = 200
shared_buffers = '4GB'                     # 内存的 25%
effective_cache_size = '12GB'              # 内存的 75%
work_mem = '64MB'                          # 每个排序/哈希操作
maintenance_work_mem = '1GB'               # VACUUM, CREATE INDEX
wal_buffers = '64MB'
random_page_cost = 1.1                     # SSD 配置
effective_io_concurrency = 200             # SSD 配置
track_io_timing = on                       # EXPLAIN ANALYZE 显示 I/O 时间
log_min_duration_statement = 200           # 慢查询日志阈值（毫秒）
```

### 监控查询

```sql
-- 查询当前运行中的慢查询
SELECT pid, now() - pg_stat_activity.query_start AS duration,
       query, state
FROM pg_stat_activity
WHERE state != 'idle'
  AND now() - pg_stat_activity.query_start > interval '5 seconds'
ORDER BY duration DESC;

-- 查询索引使用情况
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read,
       idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan ASC;

-- 查询缺失索引（来自 pg_stat_statements）
SELECT * FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 10;
```

## 参考来源

- [PostgreSQL Documentation](https://www.postgresql.org/docs/current/)
- [Use the Index, Luke!](https://use-the-index-luke.com/)
- [pganalyze – Indexing Best Practices](https://pganalyze.com/blog/5mins-postgres-indexing)
- [pgvector GitHub](https://github.com/pgvector/pgvector)
- [asyncpg Documentation](https://magicstack.github.io/asyncpg/current/)
- [PostgreSQL Wiki – Performance Optimization](https://wiki.postgresql.org/wiki/Performance_Optimization)
