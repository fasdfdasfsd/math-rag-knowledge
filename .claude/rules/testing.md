---
paths:
  - "tests/**/*.py"
description: 测试规则
---

# 测试规则

## 覆盖率要求（NON-NEGOTIABLE）
- 整体覆盖率 ≥ 80%
- 核心业务逻辑覆盖率 ≥ 90%
- PR 合并前必须通过所有测试

## 测试结构
- tests/ 目录镜像 src/ 结构
- 文件名：`test_<模块名>.py`
- 函数名：`test_<功能>_<场景>`

## Mock 策略
- 外部 API 调用使用 `pytest-asyncio` + `unittest.mock`
- 数据库测试使用测试数据库，不 mock ORM
- 禁止 mock 被测函数内部逻辑

## 断言
- 使用 `assert` 而非 `assertEqual`
- 每个测试函数 ≤ 5 个断言
- 错误场景必须有测试覆盖
