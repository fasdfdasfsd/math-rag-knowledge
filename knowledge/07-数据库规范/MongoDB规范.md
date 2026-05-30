---
category: 07-数据库规范
priority: recommended
updated: 2026-05-30
---

# MongoDB 规范

## 概述

本文档定义 MongoDB 的设计与使用规范，涵盖文档设计模式（嵌入 vs 引用）、索引策略、聚合管道优化以及使用 Python motor 驱动的最佳实践。适用于使用 MongoDB 作为文档数据库或日志/事件存储的项目。

## 核心规则

### MUST（强制遵守）

#### 文档设计——嵌入 vs 引用

- **嵌入（Embedding）**：当子文档与父文档具有强关联，且子文档独立查询需求低时，使用嵌入。
  - 典型场景：订单项（order items）、用户地址列表、博客评论。
  - 嵌入文档大小建议不超过 16MB（单文档上限）。
  - 避免无限增长的嵌入数组（如将日志嵌入用户文档）。

```javascript
// 推荐 - 嵌入（订单及其商品项）
{
    "_id": ObjectId("..."),
    "order_no": "ORD-20240530-001",
    "user_id": ObjectId("..."),
    "status": "paid",
    "items": [
        { "product_id": ObjectId("..."), "name": "Widget A", "qty": 2, "price": 49.99 },
        { "product_id": ObjectId("..."), "name": "Widget B", "qty": 1, "price": 29.99 }
    ],
    "total_amount": 129.97,
    "created_at": ISODate("2024-05-30T10:00:00Z")
}
```

- **引用（Referencing）**：当子文档独立查询频繁或数据体积大时，使用引用。
  - 典型场景：用户和文章（一对多）、商品和分类（多对多）。

```javascript
// 推荐 - 引用（评论单独集合）
// 文章文档
{
    "_id": ObjectId("..."),
    "title": "MongoDB Best Practices",
    "content": "...",
    "author_id": ObjectId("..."),
    "created_at": ISODate("2024-05-30T10:00:00Z")
}

// 评论文档（独立集合）
{
    "_id": ObjectId("..."),
    "article_id": ObjectId("..."),
    "user_id": ObjectId("..."),
    "content": "Great article!",
    "created_at": ISODate("2024-05-30T11:00:00Z")
}
// 在 article_id 上建索引
db.comments.createIndex({ "article_id": 1, "created_at": -1 });
```

#### 命名规范

- 数据库名：全小写，使用下划线分隔（`rag_knowledge`）。
- 集合名：全小写复数形式（`users`、`articles`、`comments`）。
- 字段名：全小写 snake_case（`created_at`、`display_name`、`total_amount`）。
- 字段名中禁止使用 `$` 和 `.`（MongoDB 特殊字符）。
- `_id` 字段使用 `ObjectId` 或 UUID（字符串）。

#### 索引策略

- 所有查询模式必须有对应索引支持。
- 索引命名规范：`{字段名}_{排序方向}` 或 `{字段1}_{排序}_{字段2}_{排序}`。

```javascript
// 单字段索引
db.users.createIndex({ "email": 1 }, { unique: true, name: "email_1" });

// 复合索引 - 等值条件在前，排序/范围在后
// 查询：WHERE status = 'active' ORDER BY created_at DESC
db.users.createIndex(
    { "status": 1, "created_at": -1 },
    { name: "status_1_created_at_-1" }
);

// 稀疏索引（仅对有该字段的文档建索引）
db.users.createIndex(
    { "phone": 1 },
    { sparse: true, name: "phone_1_sparse" }
);

// TTL 索引（自动过期）
db.sessions.createIndex(
    { "created_at": 1 },
    { expireAfterSeconds: 86400, name: "created_at_1_ttl_86400" }
);

// 全文索引
db.articles.createIndex(
    { "title": "text", "content": "text" },
    { name: "title_content_text" }
);
```

- 使用 `explain("executionStats")` 分析查询执行效率，关注 `totalDocsExamined` 和 `nReturned`。

```javascript
db.users.find({ "email": "test@example.com" }).explain("executionStats");
// 关注:
//   - IXSCAN (索引扫描) vs COLLSCAN (集合扫描)
//   - totalDocsExamined 应接近 nReturned
```

### SHOULD（建议遵守）

#### 查询规范

- 禁止在查询条件中使用否定操作符（`$ne`、`$nin`、`$not`）——它们通常无法高效使用索引。
- 使用投影（projection）限制返回字段，避免返回不需要的大字段。

```javascript
// 推荐 - 使用投影
db.users.find(
    { "status": "active" },
    { "email": 1, "display_name": 1, "_id": 0 }
);

// 避免 - 返回所有字段（含 content 等大字段）
db.users.find({ "status": "active" });
```

- 大结果集使用游标（cursor）分批处理，避免 `limit()` + `skip()` 深分页。
- 使用 `$in` 替代多个 `$or` 条件。

```javascript
// 推荐
db.orders.find({ "status": { "$in": ["paid", "shipped"] } });

// 避免
db.orders.find({ "$or": [{ "status": "paid" }, { "status": "shipped" }] });
```

#### 聚合管道优化

- 在聚合管道中，`$match` 和 `$sort` 尽量放在管道最前面，以利用索引。
- 使用 `$project` 尽早减少文档体积，降低后续阶段的内存压力。

```javascript
// 推荐 - 先过滤再分组
db.orders.aggregate([
    { "$match": { "status": "paid", "created_at": { "$gte": startDate } } },
    { "$group": { "_id": "$user_id", "total": { "$sum": "$total_amount" } } },
    { "$sort": { "total": -1 } },
    { "$limit": 10 }
]);

// 避免 - 先分组再过滤（所有文档都要参与分组）
db.orders.aggregate([
    { "$group": { "_id": "$user_id", "total": { "$sum": "$total_amount" } } },
    { "$match": { "total": { "$gte": 1000 } } }
]);
```

- 聚合管道的 `$lookup`（等同于 SQL JOIN）应谨慎使用，大数据集下性能较差。
- `$lookup` 关联的字段必须有索引。

#### 写操作规范

- 批量写入使用 `insert_many()` / `bulk_write()`，避免逐条插入。
- 更新使用 `update_one()` / `update_many()` 配合 `$set`，避免全文档替换。

```python
# 推荐 - 部分更新
await collection.update_one(
    {"_id": ObjectId(user_id)},
    {"$set": {"display_name": new_name, "updated_at": datetime.utcnow()}}
)

# 避免 - 全文档替换
await collection.replace_one(
    {"_id": ObjectId(user_id)},
    {"email": email, "display_name": new_name}  # 可能丢失其他字段
)
```

### MAY（可选的推荐）

- 使用 MongoDB Change Streams 监听数据变更，实现事件驱动。
- 使用 MongoDB Atlas Search 实现全文搜索（替代 Elasticsearch 的轻量方案）。
- 使用事务（MongoDB 4.0+）支持跨文档 ACID 事务（仅限副本集）。
- 考虑使用 `timeseries` 集合（MongoDB 5.0+）存储时序数据。

## 正确示例

```python
import motor.motor_asyncio
from datetime import datetime, timedelta
from bson import ObjectId
from typing import Optional


class MongoRepository:
    """Base repository for MongoDB operations using motor."""

    def __init__(self, uri: str, database: str):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(
            uri,
            maxPoolSize=50,
            minPoolSize=10,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
        )
        self.db = self.client[database]

    async def get_active_orders_since(
        self,
        days: int = 7,
        limit: int = 50,
        skip: int = 0,
    ) -> list[dict]:
        """Get active orders with pagination (cursor-based).

        Uses index on {status: 1, created_at: -1}.
        """
        since = datetime.utcnow() - timedelta(days=days)
        cursor = self.db.orders.find(
            {
                "status": {"$in": ["paid", "shipped"]},
                "created_at": {"$gte": since},
            },
            {
                "order_no": 1,
                "total_amount": 1,
                "status": 1,
                "created_at": 1,
                "items": 0,  # 排除大字段
            },
        ).sort([("created_at", -1)]).limit(limit).skip(skip)

        orders = []
        async for doc in cursor:
            doc["id"] = str(doc.pop("_id"))
            orders.append(doc)
        return orders

    async def aggregate_user_stats(self, start_date: datetime) -> list[dict]:
        """Aggregate per-user order stats using the aggregation pipeline."""
        pipeline = [
            {"$match": {"created_at": {"$gte": start_date}, "status": "paid"}},
            {"$group": {
                "_id": "$user_id",
                "order_count": {"$sum": 1},
                "total_spent": {"$sum": "$total_amount"},
                "first_order": {"$min": "$created_at"},
                "last_order": {"$max": "$created_at"},
            }},
            {"$sort": {"total_spent": -1}},
            {"$limit": 100},
            {"$project": {
                "user_id": {"$toString": "$_id"},
                "order_count": 1,
                "total_spent": 1,
                "first_order": 1,
                "last_order": 1,
                "_id": 0,
            }},
        ]
        cursor = self.db.orders.aggregate(pipeline, allowDiskUse=True)
        return [doc async for doc in cursor]

    async def close(self):
        self.client.close()
```

## 错误示例

```javascript
// 错误 1：文档设计不当 - 无限增长的嵌入数组
{
    "_id": ObjectId("..."),
    "username": "alice",
    "log_entries": [
        { "action": "login", "timestamp": ISODate("2024-01-01T00:00:00Z") },
        { "action": "view", "timestamp": ISODate("2024-01-01T01:00:00Z") },
        // ... 每月增长数千条，最终超过 16MB 文档上限
    ]
}
// 正确：将日志设计为独立集合

// 错误 2：未对查询字段建索引
db.users.find({ "email": "test@example.com" });
// email 上没有索引 -> COLLSCAN（集合扫描）

// 错误 3：$or 滥用
db.orders.find({
    "$or": [
        { "status": "pending" },
        { "status": "paid" }
    ]
});
// 使用 $in: { "status": { "$in": ["pending", "paid"] } }

// 错误 4：聚合管道顺序不当
db.orders.aggregate([
    { "$group": { "_id": "$user_id", "total": { "$sum": "$total_amount" } } },
    { "$match": { "total": { "$gte": 100 } } }  // 全量数据先分组再过滤
]);

// 错误 5：深分页
db.orders.find().sort({ "created_at": -1 }).skip(10000).limit(20);
// skip 会导致大量文档被扫描，考虑使用游标分页
// 正确：基于上一次查询的最后一个 created_at 查询
db.orders.find({ "created_at": { "$lt": last_created_at } })
    .sort({ "created_at": -1 }).limit(20);

// 错误 6：更新时使用全文档替换
db.users.updateOne(
    { "_id": ObjectId("...") },
    { "email": "new@example.com", "name": "New Name" }
);
// 这会替换整个文档，丢失其他字段！
// 正确：使用 $set

// 错误 7：大字段使用不当
// 将图片/文件存储为 Base64 字符串在文档中
{
    "_id": ObjectId("..."),
    "avatar_base64": "/9j/4AAQSkZJRg...（数 MB 的字符串）",
}
// 使用 GridFS 或外部文件存储

// 错误 8：忽略写关注
db.collection.insertOne(doc);
// 默认写关注可能不安全，生产环境应设置 w: majority
db.collection.insertOne(doc, { writeConcern: { w: "majority" } });
```

## 工具链配置

### motor 连接配置

```python
import motor.motor_asyncio

client = motor.motor_asyncio.AsyncIOMotorClient(
    "mongodb://user:pass@localhost:27017/rag_db?authSource=admin",
    maxPoolSize=50,
    minPoolSize=10,
    maxIdleTimeMS=30000,
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=5000,
    socketTimeoutMS=30000,
    retryWrites=True,
    w="majority",
    readPreference="primaryPreferred",
)
db = client.rag_knowledge
```

### MongoDB 配置优化

```yaml
# mongod.conf 关键配置
storage:
  dbPath: /data/db
  wiredTiger:
    engineConfig:
      cacheSizeGB: 4          # 物理内存的 50-80%

operationProfiling:
  mode: slowOp
  slowOpThresholdMs: 200      # 慢查询阈值
  slowOpSampleRate: 1.0

replication:
  replSetName: rs0

net:
  maxIncomingConnections: 500
```

### 监控查询

```javascript
// 查看慢查询（在 mongoshell 或 Compass 中）
db.system.profile.find({
    "millis": { "$gt": 200 }
}).sort({ "$natural": -1 }).limit(20);

// 查看索引使用情况
db.collection.aggregate([
    { "$indexStats": {} },
    { "$match": { "accesses.ops": { "$eq": 0 } } }  // 从未使用的索引
]);

// 当前操作
db.currentOp({ "active": true, "secs_running": { "$gt": 5 } });
```

## 参考来源

- [MongoDB Documentation](https://www.mongodb.com/docs/manual/)
- [MongoDB Schema Design Best Practices](https://www.mongodb.com/blog/post/building-with-patterns-a-summary)
- [MongoDB Aggregation Pipeline](https://www.mongodb.com/docs/manual/aggregation/)
- [Motor Documentation](https://motor.readthedocs.io/en/stable/)
- [MongoDB University – M201: Performance](https://university.mongodb.com/courses/M201/about)
