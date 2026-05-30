---
category: 05-编程语言规范
priority: must
updated: 2026-05-30
---

# API 与接口设计规范

## 概述

本文档定义 RESTful API 的设计标准，涵盖 URL 命名规则、HTTP 状态码使用、OpenAPI 3.1 规范、分页/排序/过滤、错误响应格式统一以及 API 版本控制策略。适用于所有对外和对内 HTTP API 服务。

## 核心规则

### MUST（强制遵守）

#### RESTful 设计原则

- 使用名词复数形式表示资源（`/users`, `/orders`, `/products`）。
- 使用 HTTP 方法表示操作：
  - `GET` – 查询资源列表或单个资源。
  - `POST` – 创建新资源。
  - `PUT` – 全量替换资源。
  - `PATCH` – 部分更新资源。
  - `DELETE` – 删除资源。
- 使用层级结构表示资源关系（`/users/{userId}/orders`）。
- 动作不应在 URL 中体现（如 `/createUser`），资源操作通过 HTTP 方法表达。
- 查询参数用于过滤、排序、分页，不用于标识资源。

```text
# 正确
GET    /users                    # 查询用户列表
GET    /users/{userId}           # 查询单个用户
POST   /users                    # 创建用户
PATCH  /users/{userId}           # 部分更新用户
DELETE /users/{userId}           # 删除用户
GET    /users/{userId}/orders    # 查询用户的订单

# 错误
GET    /getUser                  # 动词在 URL 中
POST   /createUser               # 动词在 URL 中
POST   /users/updateUser/{id}    # 动词在 URL 中，id 应在 path 参数
GET    /users/getOrders/{id}     # 嵌套资源未用层级结构
DELETE /removeUser?id=xxx        # 删除用 query param 而非 path param
```

#### HTTP 状态码

| 场景 | 状态码 |
|------|--------|
| 成功获取资源 | `200 OK` |
| 成功创建资源 | `201 Created` |
| 异步任务已接受 | `202 Accepted` |
| 成功删除资源 | `204 No Content` |
| 请求数据无效（验证失败） | `400 Bad Request` |
| 未认证 | `401 Unauthorized` |
| 无权限 | `403 Forbidden` |
| 资源不存在 | `404 Not Found` |
| 请求冲突（如重复创建） | `409 Conflict` |
| 请求过多（限流） | `429 Too Many Requests` |
| 服务器内部错误 | `500 Internal Server Error` |
| 服务暂时不可用 | `503 Service Unavailable` |

禁止：统一返回 `200 OK` 并在响应体中自定义业务状态码。必须使用 HTTP 语义的状态码。

#### 统一错误响应格式

```json
{
    "error": {
        "code": "USER_NOT_FOUND",
        "message": "User with id 'abc-123' was not found.",
        "details": [
            {
                "field": "userId",
                "message": "No user matches the given identifier.",
                "code": "NOT_FOUND"
            }
        ],
        "requestId": "req-7a1b2c3d-4e5f-6789-abcd-ef0123456789",
        "timestamp": "2026-05-30T10:30:00Z"
    }
}
```

字段说明：
- `error.code` – 机器可读的错误码（UPPER_SNAKE_CASE）。
- `error.message` – 人类可读的错误描述。
- `error.details` – 字段级别的验证错误（可选数组）。
- `error.requestId` – 请求追踪 ID（用于日志关联）。
- `error.timestamp` – 错误发生时间（ISO 8601）。

#### API 版本控制

- 版本号放在 URL 路径中：`/api/v1/users`。
- 版本号为正整数（v1, v2, v3...），不包含小版本号。
- 对于非兼容性变更（移除/重命名字段、修改端点语义）必须升级大版本。
- 对同一端点保持向后兼容至少一个版本周期。
- 默认不指定版本时，路由到最新稳定版本（通过路由重定向或 nginx 配置）。

```text
/api/v1/users       # 当前稳定版本
/api/v2/users       # 新版本（存在非兼容变更）
/api/users          # 可选：重定向到最新版本
```

#### 分页、排序、过滤

**分页标准参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `page` | integer | 1 | 页码（从 1 开始） |
| `per_page` | integer | 20 | 每页数量（最大 100） |
| `cursor` | string | - | 游标分页标记（可选，优先于 page/per_page） |

**响应格式：**

```json
{
    "data": [...],
    "pagination": {
        "page": 1,
        "per_page": 20,
        "total": 156,
        "totalPages": 8,
        "hasNext": true,
        "hasPrev": false
    }
}
```

**排序：** `?sort=created_at&order=desc` 或 `?sort=-created_at`（`-` 前缀表示降序）。

**过滤：** `?status=active&role=admin`（精确匹配），`?created_at.gte=2024-01-01`（范围查询后缀）。

### SHOULD（建议遵守）

- 使用一致的命名风格：JSON 字段使用 snake_case（Python 后端）或 camelCase（JS 前端应通过配置转换层处理）。
- GET 请求对查询参数数量有限制时返回 `414 URI Too Long` 或要求改用 POST 请求体。
- 幂等性：`GET` / `PUT` / `DELETE` 必须是幂等的；`POST` / `PATCH` 不要求幂等。
- ETag / If-None-Match 支持客户端缓存。
- 批量操作使用批量端点：`POST /users/batch`。

### MAY（可选的推荐）

- 支持部分响应（fields 参数）：`GET /users?fields=id,email`。
- 支持嵌入关联资源：`GET /users/{userId}?include=orders,profile`。
- HATEOAS 链接（超媒体作为应用状态引擎）。
- 使用 GraphQL 的场景可绕过 REST 约束，但应遵守命名规范和错误格式。

## 正确示例

### OpenAPI 3.1 规范片段

```yaml
openapi: 3.1.0
info:
  title: User Management API
  version: v1
  description: API for managing user accounts and profiles.

paths:
  /api/v1/users:
    get:
      summary: List users
      parameters:
        - name: page
          in: query
          schema:
            type: integer
            default: 1
        - name: per_page
          in: query
          schema:
            type: integer
            default: 20
            maximum: 100
        - name: status
          in: query
          schema:
            type: string
            enum: [active, inactive, suspended]
      responses:
        '200':
          description: Paginated user list
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/User'
                  pagination:
                    $ref: '#/components/schemas/Pagination'

    post:
      summary: Create a new user
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateUserRequest'
      responses:
        '201':
          description: User created successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
        '409':
          description: User with this email already exists
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

components:
  schemas:
    User:
      type: object
      properties:
        id:
          type: string
          format: uuid
        email:
          type: string
          format: email
        display_name:
          type: string
        status:
          type: string
          enum: [active, inactive]
        created_at:
          type: string
          format: date-time
    Pagination:
      type: object
      properties:
        page:
          type: integer
        per_page:
          type: integer
        total:
          type: integer
        total_pages:
          type: integer
        has_next:
          type: boolean
        has_prev:
          type: boolean
    ErrorResponse:
      type: object
      properties:
        error:
          type: object
          properties:
            code:
              type: string
            message:
              type: string
            details:
              type: array
              items:
                type: object
                properties:
                  field:
                    type: string
                  message:
                    type: string
                  code:
                    type: string
            request_id:
              type: string
            timestamp:
              type: string
              format: date-time
```

### Python FastAPI 实现

```python
from fastapi import FastAPI, HTTPException, Query, Request
from pydantic import BaseModel, EmailStr
from uuid import uuid4
from datetime import datetime, timezone

app = FastAPI(title="User Management API", version="v1")


class UserResponse(BaseModel):
    id: str
    email: str
    display_name: str | None = None
    status: str = "active"
    created_at: datetime


class Pagination(BaseModel):
    page: int
    per_page: int
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool


class PaginatedUsers(BaseModel):
    data: list[UserResponse]
    pagination: Pagination


@app.get("/api/v1/users", response_model=PaginatedUsers)
async def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: str | None = Query(None, regex="^(active|inactive|suspended)$"),
):
    """Retrieve a paginated list of users."""
    total = await get_user_count(status=status)
    users = await fetch_users(page=page, per_page=per_page, status=status)
    return PaginatedUsers(
        data=[UserResponse(**u) for u in users],
        pagination=Pagination(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=(total + per_page - 1) // per_page,
            has_next=page * per_page < total,
            has_prev=page > 1,
        ),
    )


@app.post("/api/v1/users", response_model=UserResponse, status_code=201)
async def create_user(
    payload: CreateUserRequest,
    request: Request,
):
    """Create a new user account."""
    existing = await find_user_by_email(payload.email)
    if existing:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "EMAIL_ALREADY_EXISTS",
                "message": f"User with email '{payload.email}' already exists.",
            },
        )
    user = await insert_user(
        id=str(uuid4()),
        email=payload.email,
        display_name=payload.display_name,
        created_at=datetime.now(timezone.utc),
    )
    return UserResponse(**user)
```

## 错误示例

```python
# 错误 1：URL 中使用动词
@app.post("/createUser")
async def create_user():
    ...

# 错误 2：统一返回 200
@app.get("/api/v1/users/{user_id}")
async def get_user(user_id: str):
    user = await find_user(user_id)
    if user is None:
        return {
            "code": 1001,          # 自定义业务码
            "message": "not found",
            "data": None,
        }
    return {"code": 0, "data": user}
# 正确：使用 HTTP 404

# 错误 3：删除用 GET
@app.get("/api/v1/delete-order/{order_id}")
async def delete_order(order_id: str):
    ...

# 错误 4：错误响应格式不统一
@app.get("/api/v1/users/{user_id}")
async def get_user(user_id: str):
    try:
        ...
    except Exception:
        return {"msg": "error!", "errCode": -1}
# 正确：统一 ErrorResponse 格式

# 错误 5：版本号不在路径中
@app.get("/users")
async def list_users_v1(): ...
@app.get("/users")
async def list_users_v2(): ...
# 路径冲突，无法共存

# 错误 6：分页响应结构不一致
# 不同端点返回不同分页字段：
# /api/v1/users -> {"users": [], "page": 1, "total": 100}
# /api/v1/orders -> {"orders": [], "currentPage": 1, "totalCount": 50}
# 必须统一 Pagination 模型

# 错误 7：嵌套超过 3 层
GET /api/v1/orgs/{orgId}/departments/{deptId}/users/{userId}/orders/{orderId}/items
# 考虑展平或使用查询参数

# 错误 8：缺少 requestId（无法链路追踪）
try:
    ...
except Exception:
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_ERROR", "message": "Something went wrong"}},
    )
# 需要包含 requestId
```

## 工具链配置

### FastAPI 项目结构

```text
src/
  api/
    v1/
      __init__.py
      users.py
      orders.py
    deps.py          # 公共依赖注入
  core/
    errors.py        # 统一错误模型
    pagination.py    # 分页工具
  schemas/
    common.py        # ErrorResponse, Pagination
    user.py
    order.py
```

### OpenAPI 生成与验证

```bash
# 验证 OpenAPI 规范
npx @redocly/cli lint openapi.yaml

# 生成 TypeScript 客户端
npx @openapitools/openapi-generator-cli generate \
    -i openapi.yaml \
    -g typescript-fetch \
    -o src/generated/api

# Python 服务端验证
pip install prance
prance validate openapi.yaml
```

## 参考来源

- [RESTful Web Services – Leonard Richardson & Sam Ruby](https://www.oreilly.com/library/view/restful-web-services/9780596529260/)
- [Microsoft REST API Guidelines](https://github.com/microsoft/api-guidelines)
- [OpenAPI 3.1 Specification](https://spec.openapis.org/oas/v3.1.0)
- [JSON:API Specification](https://jsonapi.org/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [OWASP REST Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html)
