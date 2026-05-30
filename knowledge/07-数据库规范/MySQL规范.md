---
category: 07-数据库规范
priority: recommended
updated: 2026-05-30
---

# MySQL 规范

## 概述

本文档定义 MySQL 数据库的设计与使用规范，涵盖 InnoDB 引擎选择、字符集 utf8mb4、查询优化最佳实践、分库分表策略概述以及索引使用规范。适用于使用 MySQL 作为关系型数据库的项目。

## 核心规则

### MUST（强制遵守）

#### 引擎与字符集

- 所有表必须使用 `InnoDB` 引擎（支持事务、行级锁、外键、崩溃恢复）。
- 字符集统一使用 `utf8mb4`，排序规则使用 `utf8mb4_unicode_ci`。
  - `utf8mb4` 支持完整 Unicode（含 emoji 和特殊字符），`utf8`（MySQL 的 utf8mb3）仅支持 BMP 字符。

```sql
-- 建表规范
CREATE TABLE users (
    id          BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    email       VARCHAR(255) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    status      VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### 表设计

- 主键推荐使用 `BIGINT UNSIGNED AUTO_INCREMENT`（分布式场景考虑雪花算法或使用 UUID 并转换为二进制存储）。
- 禁止使用 `VARCHAR` 作为主键。
- 所有表必须包含 `created_at` 和 `updated_at` 两个审计字段。
- 字段禁止使用 `TINYINT(1)` 代替 `BOOLEAN`——使用 `BOOLEAN` 或 `TINYINT(1)`（MySQL 没有原生 BOOLEAN，但语义清晰）。
- 禁止在数据库中存储明文密码、密钥等敏感信息。

```sql
-- 推荐
CREATE TABLE orders (
    id            BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id       BIGINT UNSIGNED NOT NULL,
    order_no      VARCHAR(32) NOT NULL,
    total_amount  DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    status        TINYINT NOT NULL DEFAULT 0 COMMENT '0=pending, 1=paid, 2=shipped, 3=cancelled',
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    KEY idx_user_id (user_id),
    UNIQUE KEY uidx_order_no (order_no)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### 索引规范

- 为 `WHERE`、`JOIN`、`ORDER BY` 中使用的列创建索引。
- 复合索引列顺序：高选择性列在前，低选择性列在后。
- 禁止在索引列上使用计算或函数，会导致索引失效。
- 使用 `EXPLAIN` 检查查询计划，关注 `type` 字段（`const` > `ref` > `range` > `index` > `ALL`）。
- 单表索引数量不超过 5 个（过多索引影响写入性能）。

```sql
-- 正确
CREATE INDEX idx_user_status ON orders (user_id, status);

-- 正确 - 覆盖索引
CREATE INDEX idx_order_list ON orders (user_id, status, created_at, total_amount);

-- 错误 - 函数导致索引失效
SELECT * FROM orders WHERE DATE(created_at) = '2024-06-01';
-- 应改为范围查询
SELECT * FROM orders WHERE created_at >= '2024-06-01' AND created_at < '2024-06-02';
```

#### 查询规范

- 禁止 `SELECT *`，必须显式列出所需列。
- 禁止在循环中执行单行查询（N+1 问题），使用批量查询或 JOIN。
- 大表分页避免深度 `OFFSET`，改用游标分页或子查询优化。
- 使用 `EXPLAIN` 分析执行计划，`type` 不应出现 `ALL`（全表扫描）。

```sql
-- 深度分页优化
-- 错误：OFFSET 过大
SELECT * FROM orders ORDER BY id LIMIT 20 OFFSET 100000;

-- 正确：基于上一页最后 ID 的游标分页
SELECT * FROM orders WHERE id > 100000 ORDER BY id LIMIT 20;
```

### SHOULD（建议遵守）

#### SQL 编写

- 关键字大写，表名/列名小写（同 SQL 通用规范）。
- 使用参数化查询（Prepared Statement）防止 SQL 注入。
- `JOIN` 查询中每个表使用短别名，别名限定所有列引用。
- 使用 `EXISTS` 替代 `IN` 子查询（通常性能更好）。

```sql
-- 推荐
SELECT u.id, u.email
FROM users u
WHERE EXISTS (
    SELECT 1 FROM orders o WHERE o.user_id = u.id AND o.status = 1
);

-- 避免
SELECT u.id, u.email
FROM users u
WHERE u.id IN (SELECT user_id FROM orders WHERE status = 1);
```

#### 事务使用

- 事务应尽量短小，避免在事务内包含外部 API 调用或长时间计算。
- 事务隔离级别默认使用 `READ COMMITTED`（InnoDB 默认 `REPEATABLE READ`，但 `READ COMMITTED` 更适合高并发）。
- 非核心或容忍脏读的场景考虑使用 `READ UNCOMMITTED` 提升性能。

```sql
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
START TRANSACTION;
UPDATE inventory SET quantity = quantity - 1 WHERE product_id = 1 AND quantity > 0;
INSERT INTO order_items (order_id, product_id, qty, price) VALUES (100, 1, 1, 99.00);
COMMIT;
```

#### 分库分表策略

- 水平分表：按 `user_id` 或 `order_id` 哈希取模（取模数 = 分表数量）。
- 水平分库：跨数据库实例拆分，需要引入中间件（如 ShardingSphere、MyCAT）。
- 分片键选择原则：查询率最高的列作为分片键，避免跨分片 JOIN。
- 不建议在项目初期引入分库分表——优先使用读写分离 + 缓存 + 索引优化。

### MAY（可选的推荐）

- 大字段（`TEXT`、`BLOB`、`JSON`）单独拆表，主表存指针（`id` 引用）。
- 考虑使用 `JSON` 类型存储非结构化数据（特定查询使用 `JSON_CONTAINS` 等函数）。
- 使用 `pt-online-schema-change` 或 `gh-ost` 执行大表的 DDL 变更。

## 正确示例

```sql
-- 用户订单查询（包含正确索引和参数化查询）
-- 查询某个用户最近 30 天的已支付订单，按时间降序

-- 索引设计
CREATE INDEX idx_orders_user_status_date
    ON orders (user_id, status, created_at DESC);

-- 查询 SQL（参数化）
SET @user_id = 12345;
SET @status = 1;
SET @since_date = DATE_SUB(NOW(), INTERVAL 30 DAY);

SELECT o.id,
       o.order_no,
       o.total_amount,
       o.created_at,
       oi.product_name,
       oi.quantity,
       oi.unit_price
FROM orders o
INNER JOIN order_items oi ON oi.order_id = o.id
WHERE o.user_id = @user_id
  AND o.status = @status
  AND o.created_at >= @since_date
ORDER BY o.created_at DESC
LIMIT 20;

-- 批量插入（事务保护）
START TRANSACTION;
INSERT INTO order_items (order_id, product_id, product_name, quantity, unit_price)
VALUES (1001, 1, 'Widget A', 2, 49.99),
       (1001, 2, 'Widget B', 1, 29.99);
UPDATE orders SET total_amount = 129.97, updated_at = NOW() WHERE id = 1001;
COMMIT;
```

## 错误示例

```sql
-- 错误 1：使用 MyISAM 引擎
CREATE TABLE users (
    id INT PRIMARY KEY,
    email VARCHAR(255)
) ENGINE=MyISAM;
-- MyISAM 不支持事务、行级锁，崩溃恢复差

-- 错误 2：使用旧的字符集
CREATE TABLE users (
    id INT PRIMARY KEY,
    name VARCHAR(100)
) DEFAULT CHARSET=utf8;
-- utf8（utf8mb3）不支持 4 字节字符（emoji 等）

-- 错误 3：SELECT * 且返回不必要的大字段
SELECT * FROM articles ORDER BY created_at DESC LIMIT 20;
-- 如果 articles 包含 TEXT/BLOB 大字段，大量 I/O 浪费

-- 错误 4：OR 条件导致索引失效
SELECT * FROM orders WHERE user_id = 100 OR status = 1;
-- 使用 UNION 优化或确保每个条件都有独立索引

-- 错误 5：LIKE 以 % 开头
SELECT * FROM users WHERE email LIKE '%@example.com';
-- 索引失效（除非使用 FULLTEXT 索引）
-- 如果业务需要后缀匹配，考虑反向存储

-- 错误 6：在 WHERE 条件中对索引列进行计算
SELECT * FROM orders WHERE status + 1 = 2;
-- 正确写法：WHERE status = 1

-- 错误 7：没有为外键列建索引
CREATE TABLE orders (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNSIGNED NOT NULL,
    -- user_id 没有索引，关联查询时导致 orders 全表扫描
);

-- 错误 8：字符串列使用 VARCHAR 存储固定长度数据
CREATE TABLE users (
    phone VARCHAR(20) -- 如果 phone 固定为 11 位，CHAR(11) 性能更好
);

-- 错误 9：没有使用 ON UPDATE CURRENT_TIMESTAMP
CREATE TABLE users (
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    -- 更新时不会自动刷新
);

-- 错误 10：在代码中拼接 SQL
-- Python 错误示例
cursor.execute(f"SELECT * FROM users WHERE email = '{user_input}'")
```

## 工具链配置

### MySQL 配置优化

```ini
# my.cnf 关键参数
[mysqld]
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci
innodb_buffer_pool_size = 4G        # 物理内存的 60-70%
innodb_log_file_size = 1G           # 重做日志大小
innodb_flush_log_at_trx_commit = 2  # 0=最快/最不安全, 1=最安全, 2=折中
innodb_file_per_table = 1           # 每表独立表空间
max_connections = 200
slow_query_log = 1
long_query_time = 1                 # 慢查询阈值（秒）
log_queries_not_using_indexes = 1
```

### 慢查询分析

```bash
# 查看慢查询日志
mysqldumpslow -s t /var/log/mysql/slow-query.log

# 使用 performance_schema
SELECT * FROM performance_schema.events_statements_summary_by_digest
ORDER BY SUM_TIMER_WAIT DESC
LIMIT 10;
```

### pt-query-digest 使用

```bash
pt-query-digest /var/log/mysql/slow-query.log > query_report.txt
```

## 参考来源

- [MySQL 8.0 Documentation](https://dev.mysql.com/doc/refman/8.0/en/)
- [High Performance MySQL (4th Edition) – Baron Schwartz et al.](https://www.oreilly.com/library/view/high-performance-mysql/9781492080503/)
- [MySQL Performance Blog – Percona](https://www.percona.com/blog/)
- [阿里巴巴 Java 开发手册 – MySQL 规约](https://github.com/alibaba/p3c)
- [ShardingSphere Documentation](https://shardingsphere.apache.org/documentation/)
