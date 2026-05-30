---
paths:
  - "src/api/**/*.py"
description: FastAPI 路由层约束
---

# API 路由层规则

## 职责边界（NON-NEGOTIABLE）
- 路由层**仅处理**请求解析、参数校验、响应序列化
- 禁止在路由函数中写业务逻辑 — 委托给 Service 层
- 禁止在路由函数中直接操作数据库 — 通过 Repository 层

## 契约优先（NON-NEGOTIABLE）
- 先写 OpenAPI 3.1+ spec，再实现路由
- CI 中运行 Spectral linting（`--fail-severity=error`）
- 所有错误响应遵循 RFC 9457（Problem Details + trace_id）
- 统一响应信封：`{ "data": ..., "error": null }` 或 `{ "data": null, "error": {...} }`

## 版本与兼容
- 使用 URL 路径版本（`/api/v1/`）
- 废弃端点发出 `Deprecation` + `Sunset` 响应头
- 安全变更不增加版本号（新增可选字段/端点）
- 破坏性变更 → 新版本号 + 迁移指南

## 参数校验
- 使用 Pydantic 模型做请求体验证
- 路径参数和查询参数有类型注解
- 禁止从 `request` 对象直接取未验证数据

## 速率限制
- 响应头：`X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`
- 超限返回 429 + `Retry-After`

## 异常处理
- 所有异常由全局异常处理中间件统一捕获
- 业务异常抛出 `AppException` 子类
- 路由函数中不写 try-catch
