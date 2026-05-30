---
paths:
  - "src/**/*.py"
  - "tests/**/*.py"
description: Python 编码强制规则
---

# Python 编码规则

## 类型注解（NON-NEGOTIABLE）
- 所有函数参数和返回值必须有类型注解
- 禁止使用 `Any`，特殊情况需 `# type: ignore[no-any]` 注释说明
- mypy strict 模式，零错误

## 异常处理（NON-NEGOTIABLE）
- 禁止裸 `except:`，至少捕获 `Exception`
- 禁止 `except: pass` 吞异常
- 自定义异常继承 `AppException`

## 函数与类约束
- 单函数 ≤ 50 行
- 单类 ≤ 500 行
- 圈复杂度 ≤ 10

## 可观测性（NON-NEGOTIABLE）
- 使用 `structlog`，禁止 `print()` 调试
- 日志必须包含 `correlation_id`（跨服务追踪）
- 禁止在日志中输出密码、Token、PII
- 关键操作记录 `duration_ms`（操作耗时）
- API 端点发出 RED 指标（Rate/Error/Duration）

## 文档
- Google 风格 docstring
- 中文描述

## 禁止事项
- 禁止 `import *`
- 禁止循环内数据库查询，使用批量操作
- 禁止同步 I/O 在 async 函数中
