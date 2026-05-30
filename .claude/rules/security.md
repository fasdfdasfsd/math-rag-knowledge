---
description: 安全规则（全局，始终加载）
---

# 安全规则

## 密钥管理（NON-NEGOTIABLE）
- 禁止在代码、配置文件、日志中硬编码密钥/密码/Token
- 密钥通过环境变量或密钥管理服务获取
- `.env` / `*.pem` / `*.key` / `secrets/` 不可被读取

## API 认证（NON-NEGOTIABLE）
- JWT 使用 RS256/ES256（非对称），禁止 HS256
- `alg` 从服务端 JWKS 获取，禁止信任 token header
- 必须验证 `iss`, `aud`, `exp`, `iat`
- access_token ≤ 15 分钟，refresh_token ≤ 7 天

## API 授权
- 资源访问验证所有权（Anti-BOLA）：查询按资源 owner 过滤
- 禁止从请求体绑定 `role`, `is_admin`, `tenant_id`
- 管理员操作需额外验证

## 输入验证（NON-NEGOTIABLE）
- 所有用户输入先验证后使用
- API 参数使用 Pydantic 模型校验
- 文件上传检查 MIME type + magic bytes + 大小限制

## SQL 注入防护
- 禁止字符串拼接 SQL
- 禁止使用原始 SQL 拼接用户输入
- ORM 查询参数自动参数化

## 依赖安全
- 第三方依赖使用前检查已知漏洞
- 定期 `uv lock --check` 检查依赖更新

## 日志安全
- 禁止在日志中输出密码、Token、密钥
- 禁止输出完整的用户 PII 数据
- 认证失败不区分用户存在/密码错误（响应完全一致）
