---
category: 07-数据库规范
priority: must
updated: 2026-05-30
---

# Redis 缓存规范

## 概述

本文档定义 Redis 的使用规范，涵盖数据结构选型（String / Hash / List / Set / ZSet）、Key 命名规范、TTL 设置原则、分布式锁实现、Pipeline 批量操作以及缓存穿透/击穿/雪崩的防护策略。适用于所有使用 Redis 作为缓存层和轻量级队列/存储的项目。

## 核心规则

### MUST（强制遵守）

#### Key 命名规范

格式：`{业务}:{模块}:{实体类型}:{标识}:{属性}`

```text
# 通用格式
业务:模块:实体:ID[:属性]

# 示例
rag:user:profile:u_abc123
rag:user:session:u_abc123
rag:document:embedding:doc_xyz789
rag:rate_limit:openai:ip_192.168.1.1
app:order:lock:ord_12345
```

规则：
- 使用**冒号** `:` 作为分隔符，禁止使用空格、中文等非 ASCII 字符。
- 业务/模块名使用简短英文单词全小写。
- Key 最大长度不超过 128 字节（过长消耗内存）。
- 禁止使用无前缀的通用 Key（如 `user:123` → `app:user:123`）。

#### TTL 设置原则

- 所有缓存 Key **必须**设置 TTL（Time To Live），禁止无过期时间的缓存 Key。
- TTL 遵循「业务容忍度 +/- 随机抖动」策略，避免大量 Key 同时过期。

```python
import random


def compute_ttl(base_seconds: int, jitter_ratio: float = 0.1) -> int:
    """Compute TTL with random jitter to prevent thundering herd.

    Args:
        base_seconds: Base TTL in seconds.
        jitter_ratio: Random jitter ratio (default 0.1 = ±10%).

    Returns:
        TTL with jitter applied.
    """
    jitter = int(base_seconds * jitter_ratio)
    return base_seconds + random.randint(-jitter, jitter)


# 使用示例
CACHE_TTL_USER_PROFILE = 3600       # 1 小时
CACHE_TTL_DOCUMENT = 7200           # 2 小时
CACHE_TTL_RATE_LIMIT = 60           # 1 分钟
```

- 业务缓存：5 分钟 ~ 2 小时。
- 会话缓存：30 分钟 ~ 24 小时。
- 限流计数器：1 秒 ~ 1 分钟。
- 分布式锁：根据业务最大执行时间设置，通常 5 ~ 30 秒。

#### 数据结构选择

| 场景 | 数据结构 | 说明 |
|------|----------|------|
| 缓存简单值（JSON 序列化对象） | String | `SET key value [EX]` |
| 对象多字段（如用户 profile） | Hash | `HSET user:123 name "Alice" age 30` |
| 消息队列 / 任务队列 | List | `LPUSH queue task` / `BRPOP queue timeout` |
| 去重集合 / 标签系统 | Set | `SADD tag:python doc1` |
| 排行榜 / 时间线 | ZSet | `ZADD leaderboard score user_id` |
| 位统计 / 签到 | Bitmap | `SETBIT sign:202401 user_id 1` |
| 地理空间 | Geo | `GEOADD geo:stores 116.39 39.91 "store_1"` |

- 禁止使用 String 序列化存储整个对象当 Hash 更合适时（如需要单独读写字段）。
- 避免使用 `KEYS *` 命令（阻塞），使用 `SCAN` 替代。
- 避免单个 String 存储超过 10MB 数据（大 Key 问题）。

#### 分布式锁

使用 Redis 实现分布式锁必须遵循以下规范：

```python
import asyncio
import uuid
from typing import Optional

import redis.asyncio as aioredis


class RedisDistributedLock:
    """Distributed lock implementation using Redis.

    Implements the Redlock-like algorithm with a single Redis instance.
    Uses SET NX with random value for safe release.
    """

    def __init__(
        self,
        redis: aioredis.Redis,
        lock_key: str,
        ttl_seconds: int = 10,
        retry_interval: float = 0.1,
        max_retries: int = 50,
    ):
        self.redis = redis
        self.lock_key = f"lock:{lock_key}"
        self.ttl_seconds = ttl_seconds
        self.retry_interval = retry_interval
        self.max_retries = max_retries
        self._lock_value: Optional[str] = None

    async def acquire(self) -> bool:
        """Acquire the lock with retry mechanism.

        Returns:
            True if lock acquired, False otherwise.
        """
        self._lock_value = str(uuid.uuid4())
        for attempt in range(self.max_retries):
            acquired = await self.redis.set(
                self.lock_key,
                self._lock_value,
                nx=True,
                ex=self.ttl_seconds,
            )
            if acquired:
                return True
            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.retry_interval)
        return False

    async def release(self) -> bool:
        """Release the lock safely using Lua script.

        Only releases if the value matches (prevents releasing others' locks).
        """
        if self._lock_value is None:
            return False

        # Lua script ensures atomic check-and-delete
        release_script = """
        if redis.call("GET", KEYS[1]) == ARGV[1] then
            return redis.call("DEL", KEYS[1])
        else
            return 0
        end
        """
        result = await self.redis.eval(release_script, 1, self.lock_key, self._lock_value)
        return result == 1

    async def __aenter__(self):
        acquired = await self.acquire()
        if not acquired:
            raise TimeoutError(f"Failed to acquire lock: {self.lock_key}")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.release()


# 使用示例
async def process_order(order_id: str):
    redis = aioredis.from_url("redis://localhost:6379")
    async with RedisDistributedLock(redis, f"order:{order_id}", ttl_seconds=30) as lock:
        # 临界区 - 处理重复订单保护
        ...
```

### SHOULD（建议遵守）

#### Pipeline 批量操作

当需要执行多条 Redis 命令时，使用 Pipeline 减少网络 RTT。

```python
import redis.asyncio as aioredis


async def cache_user_permissions(redis: aioredis.Redis, user_id: str, permissions: list[str]) -> None:
    """Batch cache user permissions using Pipeline."""
    key = f"app:user:perms:{user_id}"
    async with redis.pipeline(transaction=False) as pipe:
        pipe.delete(key)
        pipe.sadd(key, *permissions)
        pipe.expire(key, 3600)
        await pipe.execute()  # 一次网络往返执行所有命令
```

#### 缓存穿透防护

缓存穿透：查询不存在的数据，请求绕过缓存直达数据库。

```python
async def get_user_profile(redis: aioredis.Redis, db_pool, user_id: str) -> dict | None:
    """Get user profile with cache-penetration protection.

    Uses a short-lived empty marker to prevent repeated DB queries for non-existent keys.
    """
    cache_key = f"app:user:profile:{user_id}"

    # 1. Try cache
    cached = await redis.get(cache_key)
    if cached is not None:
        if cached == "__EMPTY__":
            return None
        return json.loads(cached)

    # 2. Query database
    user = await db_pool.fetchrow("SELECT * FROM users WHERE id = $1", user_id)

    if user is None:
        # 3. Cache empty marker (short TTL)
        await redis.setex(cache_key, 60, "__EMPTY__")
        return None

    # 4. Cache actual data
    await redis.setex(cache_key, 3600, json.dumps(dict(user)))
    return dict(user)
```

#### 缓存击穿防护

缓存击穿：热点 Key 过期瞬间，大量并发请求直达数据库。

```python
import asyncio
import aioredis


async def get_hot_data(redis: aioredis.Redis, db_pool, cache_key: str) -> dict:
    """Get hot data with mutex lock to prevent cache breakdown."""
    # 1. Try cache
    cached = await redis.get(cache_key)
    if cached is not None:
        return json.loads(cached)

    # 2. Try to acquire a distributed lock for this key
    lock_key = f"lock:rebuild:{cache_key}"
    lock_value = str(uuid.uuid4())

    locked = await redis.set(lock_key, lock_value, nx=True, ex=10)
    if locked:
        try:
            # 3. Double-check cache (another worker might have rebuilt it)
            cached = await redis.get(cache_key)
            if cached is not None:
                return json.loads(cached)

            # 4. Rebuild cache from DB
            data = await db_pool.fetchrow("SELECT * FROM hot_data WHERE key = $1", cache_key)
            result = dict(data) if data else {}
            await redis.setex(cache_key, 3600, json.dumps(result))
            return result
        finally:
            # 5. Release lock
            await redis.eval(
                "if redis.call('GET', KEYS[1]) == ARGV[1] then redis.call('DEL', KEYS[1]) end",
                1, lock_key, lock_value,
            )
    else:
        # 6. Wait for the worker that acquired the lock
        await asyncio.sleep(0.1)
        cached = await redis.get(cache_key)
        if cached:
            return json.loads(cached)

    # Fallback (rare case: lock holder crashed)
    return {}
```

#### 缓存雪崩防护

缓存雪崩：大量 Key 同时过期或 Redis 宕机导致所有请求直达数据库。

- **Key 过期分散**：基础 TTL + 随机抖动（见 TTL 原则）。
- **多级缓存**：本地缓存（`cachetools` / `caffeine`）+ Redis 远端缓存。
- **Redis 高可用**：主从 + Sentinel 或 Redis Cluster，避免单点故障。
- **限流降级**：DB 查询端设置限流，保护数据库不被冲垮。

```python
import random

BASE_TTL = 3600  # 1 hour

# 分散过期时间
ttl = BASE_TTL + random.randint(-300, 300)  # -5 min ~ +5 min
await redis.setex(cache_key, ttl, json.dumps(data))
```

### MAY（可选的推荐）

- 使用 `RedisJSON` 模块（Redis Stack）直接操作 JSON 内嵌字段。
- 使用 `RedisSearch` 模块实现全文搜索。
- 使用 `Pub/Sub` 或 `Stream` 实现事件通知（轻量级场景）。
- 使用 `HyperLogLog` 做 UV 去重计数（误差约 0.81%）。

## 正确示例

```python
import json
import hashlib
from typing import Any

import redis.asyncio as aioredis


class CacheManager:
    """Application cache manager with Redis backend."""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = aioredis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=3,
        )

    async def get_or_set(
        self,
        key: str,
        fetch_func: callable,
        ttl: int = 3600,
        empty_ttl: int = 60,
    ) -> Any:
        """Cache-aside pattern with empty-value protection."""
        cached = await self.redis.get(key)
        if cached is not None:
            if cached == "__EMPTY__":
                return None
            return json.loads(cached)

        data = await fetch_func()

        if data is None:
            await self.redis.setex(key, empty_ttl, "__EMPTY__")
            return None

        await self.redis.setex(key, ttl, json.dumps(data, default=str))
        return data

    async def invalidate(self, pattern: str) -> int:
        """Invalidate all keys matching a pattern."""
        cursor = 0
        deleted = 0
        while True:
            cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
            if keys:
                deleted += await self.redis.delete(*keys)
            if cursor == 0:
                break
        return deleted

    async def close(self):
        await self.redis.close()


# 使用示例
cache = CacheManager()
user = await cache.get_or_set(
    key=f"app:user:profile:{user_id}",
    fetch_func=lambda: fetch_user_from_db(user_id),
    ttl=3600,
    empty_ttl=60,
)
```

## 错误示例

```python
# 错误 1：Key 命名无规范
await redis.set("abc123", data)           # 含义不明
await redis.set("用户:123", data)          # 包含中文
await redis.set("a_very_long_key_" * 20, data)  # 长度过长

# 错误 2：没有设置 TTL
await redis.set("app:user:profile:123", json.dumps(user))
# Key 永远不会过期，内存无限增长

# 错误 3：大 Key 存储
await redis.set("app:log:big_data", json.dumps(large_list))
# 单个 String > 10MB，阻塞 Redis 和网络

# 错误 4：分布式锁缺少安全释放机制
# 错误：只用 DEL，没有检查 value
await redis.delete(lock_key)
# 如果锁已被其他进程获取，此操作会释放别人的锁

# 错误 5：在热点 Key 上使用 KEYS *
keys = await redis.keys("app:user:*")
# KEYS 会阻塞 Redis，生产环境应使用 SCAN

# 错误 6：缓存穿透无防护
async def get_user(user_id: str):
    cached = await redis.get(f"app:user:{user_id}")
    if cached:
        return json.loads(cached)
    # 如果数据库中也不存在此用户，每次请求都会查 DB
    user = await db.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
    if user:
        await redis.setex(f"app:user:{user_id}", 3600, json.dumps(dict(user)))
    return user

# 错误 7：Pipeline 多命令时忘记 execute
pipe = redis.pipeline()
pipe.set("k1", "v1")
pipe.set("k2", "v2")
pipe.get("k1")
# 忘记调用 pipe.execute()，命令不会执行

# 错误 8：在循环中逐条执行命令
for key in many_keys:
    await redis.get(key)  # N 次网络往返
# 应使用 MGET/SDIFF/UNION 等批量操作或 Pipeline

# 错误 9：使用过大的集合（百万级 Set），而没有考虑迁移方案
# 定期清理或启用 Redis 内存淘汰策略（如 allkeys-lru）

# 错误 10：将 Redis 当作主数据库使用
# Redis 应作为缓存层，重要数据必须有持久化存储（PostgreSQL/MySQL）
```

## 工具链配置

### Redis 配置优化

```ini
# redis.conf 关键参数
maxmemory 4gb
maxmemory-policy allkeys-lru
timeout 300
tcp-keepalive 60
lazyfree-lazy-eviction yes
lazyfree-lazy-expire yes
slowlog-log-slower-than 10000
slowlog-max-len 128
```

### Python redis.asyncio 连接配置

```python
import redis.asyncio as aioredis

redis = aioredis.from_url(
    "redis://:password@localhost:6379/0",
    encoding="utf-8",
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=5,
    retry_on_timeout=True,
    health_check_interval=30,
    max_connections=50,
)
```

### 监控命令

```bash
# 查看 Key 分布
redis-cli --bigkeys

# 慢查询
redis-cli SLOWLOG GET 10

# 监控实时命令
redis-cli MONITOR

# 内存使用
redis-cli INFO memory
```

## 参考来源

- [Redis Documentation](https://redis.io/documentation)
- [Redis Distributed Locks – Martin Kleppmann](https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html)
- [Redlock Algorithm](https://redis.io/docs/manual/patterns/distributed-locks/)
- [Redis in Action – Josiah L. Carlson](https://www.manning.com/books/redis-in-action)
- [aws/elasticache – Best Practices](https://docs.aws.amazon.com/AmazonElastiCache/latest/red-ug/BestPractices.html)
