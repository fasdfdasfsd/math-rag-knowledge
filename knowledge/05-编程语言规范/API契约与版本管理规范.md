---
category: 编程语言规范
type: spec
priority: must
version: 1.0
updated: 2026-05-30
enforced_by:
  - ci: Spectral linting
  - ci: Breaking change detection
---

# API 契约与版本管理规范

## 一、契约优先（Contract-First）

### 原则
- OpenAPI 3.1+ spec 是**权威交付物**，先写 spec 再写代码
- 从 spec 生成 server stub、client SDK、mock server
- CI 中运行 Spectral linting（`--fail-severity=error`）
- 禁止从代码反向生成 spec 作为主要文档源

### 错误响应格式
```json
{
  "type": "https://api.example.com/errors/validation-error",
  "title": "Validation Error",
  "status": 422,
  "detail": "The 'email' field is required.",
  "instance": "/users/123",
  "trace_id": "abc-123-def"
}
```
遵循 RFC 9457（Problem Details），所有错误响应包含 `trace_id`。

## 二、版本策略

### 推荐：URL 路径版本
```
/api/v1/users
/api/v2/users
```
企业默认方案：路由明确，文档和 API 管理工具支持最好。

### 其他策略
| 策略 | 适用场景 |
|------|----------|
| Header (`X-API-Version`) | 内部 API，多个表现层 |
| 日期（Stripe 风格） | 快速发布节奏 |
| 无显式版本 | 仅内部 API，强向后兼容 |

### 版本数量限制
- 同时支持最多 **2-3 个**主要版本
- 旧版本有明确的退役时间线

## 三、向后兼容规则

### 安全变更（不增加主版本号）
- ✅ 新增可选字段
- ✅ 新增端点
- ✅ 新增可选查询参数
- ✅ 放宽校验（required → optional）
- ✅ 新增枚举值

### 破坏性变更（需主版本号 + 迁移指南）
- ❌ 删除/重命名字段
- ❌ 改变字段类型
- ❌ 可选→必填
- ❌ 删除端点
- ❌ 改变认证方式

## 四、废弃生命周期

```http
Deprecation: Wed, 31 Dec 2026 23:59:59 GMT
Sunset: Wed, 30 Jun 2027 23:59:59 GMT
Link: <https://api.example.com/docs/migration-v2>; rel="deprecation"
```

- 废弃通知最少 **6 个月**
- 所有废弃端点的响应头包含 `Deprecation` + `Sunset`
- 监控旧版本流量，>10% 告警

## 五、速率限制

- 响应头：`X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`
- 超限返回 429 + `Retry-After`
- 分级：IP（100/min）、用户（1000/min）、关键端点（10/min）
