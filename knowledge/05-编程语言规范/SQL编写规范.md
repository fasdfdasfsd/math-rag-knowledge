---
category: 05-编程语言规范
priority: must
updated: 2026-05-30
---

# SQL 编写规范

## 概述

本文档定义项目中所有 SQL 语句的编写规范，涵盖 SQL 关键字格式、标识符命名、查询优化、参数化查询防御 SQL 注入、索引使用原则以及 JOIN 优化策略。适用于 PostgreSQL 和 MySQL 两种主流数据库。

## 核心规则

### MUST（强制遵守）

#### 关键字与标识符格式

- SQL 关键字一律大写（`SELECT`, `FROM`, `WHERE`, `JOIN`, `INSERT`, `UPDATE`, `DELETE`, `CREATE`, `ALTER`, `DROP` 等）。
- 表名、列名、索引名等标识符一律小写，使用下划线分隔（snake_case）。
- 表名使用复数形式（`users`, `orders`, `order_items`）。
- 列名不使用保留关键字，避免加引号包裹。

```sql
-- 正确
SELECT id, user_id, created_at
FROM orders
WHERE status = 'active'
ORDER BY created_at DESC;

-- 错误
select id, userId, createdat from orders where Status = 'active';
SELECT Id, UserId, CreatedAt FROM Orders;  -- 大小写不统一
```

#### 禁止 SELECT *

```sql
-- 禁止
SELECT * FROM users;

-- 必须显式列出需要的列
SELECT id, email, display_name, created_at FROM users;
```

原因：
1. 容易读取不需要的列，增加 I/O 和网络传输。
2. JOIN 时多表同名列会冲突。
3. 表结构变化时隐式改变结果集，可能导致应用程序异常。

#### 参数化查询

所有动态 SQL 必须使用参数化查询（Prepared Statement），**禁止** 字符串拼接构造 SQL。

```python
# 正确 - asyncpg 参数化（$1, $2）
async def get_user(pool: asyncpg.Pool, user_id: str) -> dict | None:
    query = "SELECT id, email, display_name FROM users WHERE id = $1"
    row = await pool.fetchrow(query, user_id)
    return dict(row) if row else None


# 错误 - 字符串拼接（SQL 注入风险）
async def get_user(pool: asyncpg.Pool, user_id: str) -> dict | None:
    query = f"SELECT id, email, display_name FROM users WHERE id = '{user_id}'"
    row = await pool.fetchrow(query)
    return dict(row) if row else None
```

```python
# 正确 - psycopg2 / psycopg3（%s 占位符）
cursor.execute(
    "SELECT id, email FROM users WHERE email = %s",
    (email,),
)

# 错误 - 字符串拼接
cursor.execute(
    f"SELECT id, email FROM users WHERE email = '{email}'",
)
```

```python
# 正确 - SQLAlchemy ORM
result = await session.execute(
    select(User).where(User.email == email)
)
```

#### WHERE 条件使用索引列

- `WHERE` 子句中的过滤条件应尽量匹配已有索引。
- 避免在索引列上使用函数包装：`WHERE DATE(created_at) = '2024-01-01'` → 应该用范围查询：`WHERE created_at >= '2024-01-01' AND created_at < '2024-01-02'`。
- 避免在索引列上做隐式类型转换。

```sql
-- 正确 - 使用范围查询
SELECT id, email
FROM users
WHERE created_at >= '2024-01-01'
  AND created_at < '2024-01-02';

-- 错误 - 函数包装导致索引失效
SELECT id, email
FROM users
WHERE DATE(created_at) = '2024-01-01';
```

#### JOIN 规范

- JOIN 必须显式使用 `INNER JOIN` / `LEFT JOIN` / `RIGHT JOIN` 关键字，避免隐式逗号连接。
- 每个表必须有短别名（2-4 个字母），在 ON 和 SELECT 中使用别名限定列名。
- 关联条件必须使用 `ON` 子句，禁止将关联条件放在 `WHERE` 中。

```sql
-- 正确
SELECT u.id, u.email, o.id AS order_id, o.total_amount
FROM users u
INNER JOIN orders o ON o.user_id = u.id
WHERE u.status = 'active';

-- 错误 - 隐式 JOIN + 关联条件在 WHERE
SELECT u.id, u.email, o.id, o.total_amount
FROM users u, orders o
WHERE o.user_id = u.id
  AND u.status = 'active';
```

### SHOULD（建议遵守）

#### INSERT 显式指定列

```sql
-- 正确
INSERT INTO users (id, email, display_name, status)
VALUES ($1, $2, $3, 'active');

-- 避免 - 依赖列顺序
INSERT INTO users VALUES ($1, $2, $3, 'active');
```

#### 分页查询

- 推荐使用基于游标的分页（cursor-based pagination），特别是大数据量场景。
- 传统 `OFFSET` / `LIMIT` 分页在深分页时性能急剧下降。

```sql
-- 游标分页（推荐）
SELECT id, email, created_at
FROM users
WHERE created_at < $1  -- 上一次查询的最后一条 created_at
ORDER BY created_at DESC
LIMIT 20;

-- OFFSET 分页（仅适用于小数据集）
SELECT id, email, created_at
FROM users
ORDER BY created_at DESC
LIMIT 20 OFFSET 40;
```

#### 事务使用

- 多表更新必须使用事务，确保原子性。
- 事务内避免长查询和外部 API 调用，减少锁持有时间。

```sql
BEGIN;
UPDATE inventory SET quantity = quantity - 1 WHERE product_id = $1 AND quantity > 0;
INSERT INTO order_items (order_id, product_id, quantity, price) VALUES ($2, $1, 1, $3);
COMMIT;
```

#### 子查询 vs JOIN

- 优先使用 JOIN 而非子查询（通常性能更好、优化器处理更佳）。
- 必须使用子查询时，优先使用 `EXISTS` 而非 `IN`（尤其子查询结果集较大时）。

```sql
-- 推荐 - EXISTS
SELECT u.id, u.email
FROM users u
WHERE EXISTS (
    SELECT 1 FROM orders o WHERE o.user_id = u.id AND o.status = 'paid'
);

-- 避免 - 大结果集的 IN 子查询
SELECT u.id, u.email
FROM users u
WHERE u.id IN (
    SELECT user_id FROM orders WHERE status = 'paid'
);
```

### MAY（可选的推荐）

- 使用 CTE（`WITH` 子句）提高复杂查询的可读性。
- 大表分页可以考虑键集分页（keyset pagination）：`WHERE (created_at, id) < ($1, $2)`。
- 使用 `EXPLAIN ANALYZE` 评估查询计划（见数据库规范文档）。

## 正确示例

```sql
-- 查询用户及其最近订单
SELECT
    u.id          AS user_id,
    u.email,
    u.display_name,
    o.id          AS order_id,
    o.total_amount,
    o.created_at  AS order_date
FROM users u
INNER JOIN orders o ON o.user_id = u.id
WHERE u.status = 'active'
  AND o.status IN ('paid', 'shipped')
  AND o.created_at >= '2024-06-01'
ORDER BY o.created_at DESC
LIMIT 20;

-- 批量更新（事务）
BEGIN;
UPDATE order_items
SET quantity = quantity + 1
WHERE order_id = $1 AND product_id = $2;

UPDATE orders
SET total_amount = total_amount + $3,
    updated_at = NOW()
WHERE id = $1;
COMMIT;

-- CTE 递归查询（组织树）
WITH RECURSIVE org_tree AS (
    SELECT id, name, parent_id, 1 AS depth
    FROM org_units
    WHERE parent_id IS NULL
    UNION ALL
    SELECT o.id, o.name, o.parent_id, t.depth + 1
    FROM org_units o
    INNER JOIN org_tree t ON o.parent_id = t.id
)
SELECT * FROM org_tree ORDER BY depth, name;
```

## 错误示例

```sql
-- 错误 1：SELECT *
SELECT * FROM users WHERE email = 'test@example.com';

-- 错误 2：字符串拼接（SQL 注入）
-- Python 中的错误写法
query = f"SELECT * FROM users WHERE email = '{user_input}'"

-- 错误 3：隐式 JOIN
SELECT u.name, o.total
FROM users u, orders o
WHERE u.id = o.user_id;

-- 错误 4：在 WHERE 条件中对索引列使用函数
SELECT * FROM orders WHERE DATE(created_at) = CURRENT_DATE;

-- 错误 5：不指定列的 INSERT
INSERT INTO users VALUES ('abc', 'test@example.com', 'Test', NOW());
-- 如果表结构变化将导致错误或数据错位

-- 错误 6：使用 OR 条件导致索引失效
SELECT * FROM users WHERE email = 'a@b.com' OR phone = '123456';
-- 可以改为 UNION
SELECT * FROM users WHERE email = 'a@b.com'
UNION
SELECT * FROM users WHERE phone = '123456';

-- 错误 7：LIKE 以通配符开头
SELECT * FROM products WHERE name LIKE '%keyword%';  -- 索引失效
-- 如果必须全文搜索，考虑使用全文索引（PostgreSQL tsvector / MySQL FULLTEXT）

-- 错误 8：OFFSET 分页过深
SELECT * FROM users ORDER BY id LIMIT 20 OFFSET 100000;  -- 越往后越慢
```

## 工具链配置

### SQLFluff（SQL Linter）

```ini
[sqlfluff]
dialect = postgres
max_line_length = 120

[sqlfluff:rules]
capitalisation.keywords = upper
capitalisation.functions = upper
capitalisation.literals = upper

[sqlfluff:indentation]
indent_unit = space
tab_space_size = 4
```

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/sqlfluff/sqlfluff
    rev: 3.0.0
    hooks:
      - id: sqlfluff-lint
        args: [--dialect, postgres]
      - id: sqlfluff-fix
        args: [--dialect, postgres]
```

## 参考来源

- [PostgreSQL Documentation – SQL Syntax](https://www.postgresql.org/docs/current/sql-syntax.html)
- [MySQL Documentation – SQL Statement Syntax](https://dev.mysql.com/doc/refman/8.0/en/sql-statements.html)
- [SQLFluff Documentation](https://docs.sqlfluff.com/)
- [Use the Index, Luke! – A Guide to Database Performance](https://use-the-index-luke.com/)
- [OWASP SQL Injection Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html)
