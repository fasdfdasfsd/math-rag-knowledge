---
paths:
  - "src/repositories/**/*.py"
  - "src/models/**/*.py"
description: 数据库操作约束
---

# 数据库规则

## 查询安全（NON-NEGOTIABLE）
- 禁止直接拼接 SQL 字符串
- 使用 SQLAlchemy ORM 或参数化查询
- 动态排序字段必须白名单校验

## 性能要求
- 禁止循环内数据库查询 — 使用批量操作
- 复杂查询检查执行计划，禁止全表扫描
- 连接池配置：通过 FastAPI Depends 注入

## ORM 模型规范
- 表名列名遵循命名规范（snake_case）
- 每个模型有 `created_at` / `updated_at`
- 外键显式定义 `ondelete` 行为

## 迁移
- 使用 Alembic 管理数据库迁移
- 禁止手动修改数据库 schema
