---
category: 安全规范
type: spec
priority: must
version: 1.0
updated: 2026-05-30
enforced_by:
  - hook: Read deny .pem/.key/secrets
  - linter: ruff (S608 SQL injection)
  - advisory
---

# API 安全规范

## 一、认证（Authentication）

### JWT 规范
- 算法：RS256 或 ES256（非对称），禁止 HS256
- 有效期：access_token ≤ 15 分钟，refresh_token ≤ 7 天
- 必须验证：`iss`, `aud`, `exp`, `iat`
- `alg` 从服务端 JWKS 获取，禁止信任 token header

### OAuth 2.0 / OIDC
- 用户认证用 Authorization Code + PKCE
- 服务间认证用 Client Credentials
- 禁止自定义认证方案

## 二、授权（Authorization）

### 最小权限
- 每个 API 端点声明所需 scope
- 资源访问验证所有权（Anti-BOLA）
- 管理员操作需额外验证

### 禁止
- 通过隐藏 URL 实现"安全性"
- 在客户端做权限判断
- 从请求体绑定 `role`, `is_admin`, `tenant_id`

## 三、输入验证

### 所有输入不可信
- Pydantic 模型验证所有请求体
- 路径参数和查询参数做类型 + 范围校验
- 文件上传：检查 MIME type + magic bytes + 大小限制

### 注入防护
- SQL：使用参数化查询 / ORM，禁止拼接
- NoSQL：验证操作符白名单
- 命令注入：禁止 `os.system()` / `subprocess(shell=True)`

## 四、传输安全

- 全站 TLS 1.3（最低 TLS 1.2）
- HSTS 头：`max-age=31536000; includeSubDomains`
- 禁止在 URL 中传递敏感参数
- API Key 放 Header，不放 Query String

## 五、速率限制

- 按 IP：100 req/min
- 按用户：1000 req/min
- 按关键端点（登录/注册）：10 req/min
- 超限返回 429 + `Retry-After` 头

## 六、安全测试

- SAST（Semgrep）在 CI 中运行
- 依赖扫描（Trivy/Snyk）
- 密钥扫描（Gitleaks）在 pre-commit hook
- DAST（OWASP ZAP）对 staging 环境
