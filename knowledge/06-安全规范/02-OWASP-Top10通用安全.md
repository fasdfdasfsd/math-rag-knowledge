---
category: 安全规范
priority: must
updated: 2026-05-30
---

# OWASP Top 10 通用 Web 安全风险

## 概述

OWASP Top 10（2021 版）是 Web 应用安全领域最权威的风险清单。本文件将 10 类风险映射到 Python/FastAPI 项目的具体防范实践，涵盖 RAG 系统的 API 层、检索服务、文档管理入口的安全防护。

---

## 核心规则
### 🔴 必须遵守 (MUST)

---

### A01: Broken Access Control（访问控制失效）

**描述**：访问控制机制未正确实施，用户可越权访问未授权的资源。在 RAG 场景中表现为用户可检索到无权限的文档。

**影响**：
- 越权访问敏感文档
- 权限提升
- 数据泄露

**Python/FastAPI 防范示例**：

```python
from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

app = FastAPI()
security = HTTPBearer()

# ===== 基于 RBAC 的文档访问控制 =====
class DocumentPermission:
    """文档权限校验中间件"""

    @staticmethod
    def verify_access(
        user_id: str,
        document_id: str,
        required_role: str = "reader",
    ) -> bool:
        """
        验证用户是否有权访问文档。
        在生产环境中应查询权限数据库。
        """
        # 权限检查逻辑
        user_roles = get_user_roles(user_id)  # 从数据库获取
        doc_permissions = get_doc_permissions(document_id)

        if required_role not in user_roles:
            raise HTTPException(status_code=403, detail="权限不足")
        if user_id not in doc_permissions.get("allowed_users", []):
            raise HTTPException(status_code=403, detail="无文档访问权限")
        return True


@app.get("/api/v1/documents/{document_id}")
async def get_document(
    document_id: str,
    credentials: HTTPAuthorizationCredentials = Security(security),
):
    """获取文档（含访问控制）"""
    user_id = decode_token(credentials.credentials)  # 从 JWT 解析用户
    DocumentPermission.verify_access(user_id, document_id, "reader")

    document = await query_document(document_id)
    return document
```

**错误示例**：
```python
# 🚫 错误：未做访问控制
@app.get("/api/v1/documents/{document_id}")
async def get_document(document_id: str):
    # 任何人都可以访问任何文档！
    return get_document_from_db(document_id)


# ✅ 正确：必须校验身份和权限
@app.get("/api/v1/documents/{document_id}")
async def get_document_secured(
    document_id: str,
    user: User = Depends(get_current_user),
):
    if not user.can_read(document_id):
        raise HTTPException(status_code=403)
    return get_document_from_db(document_id)
```

---

### A02: Cryptographic Failures（加密失败）

**描述**：使用弱加密算法、不安全的密钥管理或未加密传输敏感数据。

**影响**：
- 敏感数据明文传输被窃听
- 加密被破解
- 密钥泄露

**Python/FastAPI 防范示例**：

```python
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers import algorithms, modes

# ===== 加密实践 =====

# ✅ 正确：使用 AES-256-GCM（当前推荐）
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

def encrypt_sensitive_data(data: bytes, key: bytes) -> bytes:
    """使用 AES-256-GCM 加密"""
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)  # GCM 推荐 12 字节 nonce
    return nonce + aesgcm.encrypt(nonce, data, None)

def decrypt_sensitive_data(encrypted: bytes, key: bytes) -> bytes:
    """解密 AES-256-GCM 数据"""
    aesgcm = AESGCM(key)
    nonce, ciphertext = encrypted[:12], encrypted[12:]
    return aesgcm.decrypt(nonce, ciphertext, None)


# ===== FastAPI 强制 HTTPS =====
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*.example.com"],
)

# ✅ 正确：配置 HSTS 头
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response
```

**错误示例**：
```python
# 🚫 错误：使用 MD5 或 SHA-1 做安全哈希
import hashlib
password_hash = hashlib.md5(password.encode()).hexdigest()  # 不安全！

# ✅ 正确：使用 bcrypt/argon2 哈希密码
from passlib.hash import bcrypt
password_hash = bcrypt.hash(password)
```

---

### A03: Injection（注入攻击）

**描述**：不可信数据作为命令或查询的一部分发送到解释器，包括 SQL 注入、NoSQL 注入、OS 命令注入等。

**影响**：
- 数据泄露
- 数据篡改或删除
- 远程代码执行

**Python/FastAPI 防范示例**：

```python
# ===== SQL 注入防护 =====

# ✅ 正确：使用参数化查询
import sqlite3

def get_user_by_id(user_id: int):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    # 参数化查询 — 安全
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    return cursor.fetchone()


# ✅ 正确：使用 ORM（SQLAlchemy）
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

def get_user_orm(user_id: int):
    engine = create_engine("sqlite:///users.db")
    with Session(engine) as session:
        # 安全：ORM 自动参数化
        result = session.execute(
            text("SELECT * FROM users WHERE id = :id"),
            {"id": user_id}
        )
        return result.fetchone()


# ===== NoSQL 注入防护（MongoDB）=====
def query_user_safe(user_input: str):
    """安全的 MongoDB 查询"""
    from pymongo import MongoClient
    client = MongoClient()

    # 🚫 错误：直接拼接
    # db.users.find({"$where": f"this.name == '{user_input}'"})

    # ✅ 正确：使用参数化
    db.users.find({"name": {"$regex": re.escape(user_input)}})
```

**错误示例**：
```python
# 🚫 错误：字符串拼接 SQL 查询（极其危险！）
def get_user_by_name(name: str):
    cursor.execute(f"SELECT * FROM users WHERE name = '{name}'")
    # 攻击者输入: ' OR '1'='1  → 返回所有用户！
    return cursor.fetchall()
```

---

### A04: Insecure Design（不安全设计）

**描述**：在架构设计阶段缺乏安全考虑，导致后续难以修复的漏洞。

**影响**：
- 架构级安全缺陷
- 修复成本高昂
- 系统性风险

**Python/FastAPI 防范示例**：

```python
# ===== 安全设计原则 =====

# 1. 最小权限原则：API 端点明确指定所需权限
from enum import Enum

class Permission(Enum):
    DOCUMENT_READ = "document:read"
    DOCUMENT_WRITE = "document:write"
    DOCUMENT_DELETE = "document:delete"
    USER_MANAGE = "user:manage"


def require_permission(permission: Permission):
    """权限装饰器"""
    from functools import wraps

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user = get_current_user()  # 从上下文中获取
            if permission.value not in user.permissions:
                raise HTTPException(
                    status_code=403,
                    detail=f"需要 {permission.value} 权限"
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# 2. 默认安全：新端点默认需要认证
class DefaultAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # 白名单路径不需要认证
        public_paths = {"/health", "/docs", "/openapi.json"}
        if request.url.path not in public_paths:
            # 验证认证 Token
            auth = request.headers.get("Authorization")
            if not auth or not verify_token(auth):
                return JSONResponse(
                    status_code=401,
                    content={"detail": "需要认证"}
                )
        return await call_next(request)
```

---

### A05: Security Misconfiguration（安全配置错误）

**描述**：安全配置不当，如启用调试模式、默认凭据、不安全的 CORS 配置、不必要的开放端口。

**影响**：
- 信息泄露（调试信息）
- 未授权访问
- 服务被利用

**Python/FastAPI 防范示例**：

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ===== CORS 安全配置 =====

# ✅ 正确：明确指定允许的源
app = FastAPI(docs_url=None, redoc_url=None)  # 生产环境禁用自动文档

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.example.com"],  # 明确指定，不用 ["*"]
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # 仅允许必要方法
    allow_headers=["Authorization", "Content-Type"],
)


# ===== 环境感知配置 =====
from pydantic_settings import BaseSettings

class AppConfig(BaseSettings):
    # 自动根据环境加载配置
    environment: str = "development"
    debug: bool = False

    # 生产环境强制关闭调试
    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    # 自动验证
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.is_production and self.debug:
            raise ValueError("生产环境不能开启 debug 模式！")


config = AppConfig()
app.debug = config.debug

# 生产环境禁用调试路由
if config.is_production:
    app.docs_url = None
    app.redoc_url = None
```

**错误示例**：
```python
# 🚫 错误：生产环境开启 debug
app = FastAPI(debug=True)  # 暴露详细错误信息！

# 🚫 错误：CORS 允许所有来源
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 任何网站都可以跨域请求
    allow_credentials=True,  # 与 allow_origins=["*"] 冲突，会使 Cookie 失效
)
```

---

### A06: Vulnerable and Outdated Components（易受攻击组件）

**描述**：使用存在已知漏洞的第三方库和框架。

**影响**：
- 已知漏洞被利用
- 供应链攻击

**Python/FastAPI 防范示例**：

```python
# ===== 依赖安全检查 =====

"""
# 1. 使用 pip-audit 扫描已知漏洞
pip install pip-audit
pip-audit --requirement requirements.txt --desc on

# 2. 使用 safety 检查
pip install safety
safety check --file requirements.txt

# 3. CI/CD 集成（GitHub Actions 示例）
# .github/workflows/security-scan.yml
name: Security Scan
on: [push, pull_request]
jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install pip-audit
      - run: pip-audit --requirement requirements.txt
"""

# ===== 依赖版本策略 =====
# pyproject.toml
"""
[tool.pip-audit]
ignore-vulnerabilities = []  # 不要忽略漏洞——及时修复

[tool.pip-licenses]
allowed-licenses = [
    "MIT", "Apache-2.0", "BSD-3-Clause", "BSD-2-Clause",
    "MPL-2.0", "LGPL-3.0-only",
]
disallowed-licenses = ["GPL-3.0-only", "AGPL-3.0-only"]

[tool.uv]
dev-dependencies = []
"""
```

---

### A07: Identification and Authentication Failures（认证失败）

**描述**：身份验证机制存在缺陷，如弱密码策略、Session 固定、凭据填充、暴力破解。

**影响**：
- 账户被盗
- 暴力破解成功
- Session 劫持

**Python/FastAPI 防范示例**：

```python
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
import jwt

# ===== 安全的密码管理 =====
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,  # 足够高的轮次
)

def hash_password(password: str) -> str:
    """安全的密码哈希"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


# ===== JWT 安全实践 =====
JWT_SECRET_KEY: str = ""  # 从环境变量加载！
JWT_ALGORITHM = "RS256"  # 使用非对称算法
ACCESS_TOKEN_EXPIRE_MINUTES = 15  # 短过期时间
REFRESH_TOKEN_EXPIRE_DAYS = 7


def create_access_token(data: dict) -> str:
    """创建短期访问令牌"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """创建刷新令牌"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


# ===== 登录频率限制 =====
from fastapi import Request
from fastapi.responses import JSONResponse
import time

login_attempts: dict[str, list[float]] = {}

def check_login_rate_limit(identifier: str, max_attempts: int = 5, window: int = 300):
    """登录频率限制：同一 IP/用户 5 分钟内最多尝试 5 次"""
    now = time.time()
    attempts = login_attempts.get(identifier, [])
    # 清除过期记录
    attempts = [t for t in attempts if t > now - window]

    if len(attempts) >= max_attempts:
        raise HTTPException(
            status_code=429,
            detail=f"登录尝试过于频繁，请在 {window // 60} 分钟后重试"
        )

    attempts.append(now)
    login_attempts[identifier] = attempts
```

**错误示例**：
```python
# 🚫 错误：使用 MD5 加密密码
import hashlib
hashed = hashlib.md5(password.encode()).hexdigest()  # 可被秒速破解！

# 🚫 错误：JWT 使用弱算法
token = jwt.encode(payload, "secret", algorithm="HS256")  # 对称算法，密钥泄露可伪造
# 使用 HS256 时密钥泄露，攻击者可伪造任意 Token
```

---

### A08: Software and Data Integrity Failures（软件和数据完整性故障）

**描述**：未验证软件更新或数据的完整性，使用未签名的代码或未校验来源的数据。

**影响**：
- 恶意代码注入
- 数据篡改
- 供应链攻击

**Python/FastAPI 防范示例**：

```python
import hashlib
import requests
from typing import Optional

class SoftwareIntegrityVerifier:
    """软件包完整性校验"""

    @staticmethod
    def verify_package_hash(
        package_name: str,
        version: str,
        downloaded_file: str,
        expected_hash: str,
    ) -> bool:
        """验证下载包的哈希值"""
        h = hashlib.sha256()
        with open(downloaded_file, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)

        actual = h.hexdigest()
        if actual != expected_hash:
            raise ValueError(
                f"包 {package_name}=={version} 哈希不匹配！"
                f"预期: {expected_hash}, 实际: {actual}"
            )
        return True


# ===== pip 包签名验证配置 =====
"""
# 在 pip.conf 或 pyproject.toml 中启用包签名验证

[tool.uv]
verify-hashes = true

# requirements.txt 使用哈希锁定
uv add --hash sha256:xxx --hash sha256:yyy package==1.0.0
"""
```

---

### A09: Security Logging and Monitoring Failures（日志监控失败）

**描述**：安全日志记录和监控不足，导致无法及时发现和响应安全事件。

**影响**：
- 安全事件未被发现
- 无法进行事件溯源
- 违反合规要求（GDPR/PIPL 要求的日志记录）

**Python/FastAPI 防范示例**：

```python
import logging
import json
from datetime import datetime, timezone
from fastapi import Request, Response
import time

# ===== 结构化安全日志 =====
class SecurityLogger:
    """安全事件日志记录器"""

    def __init__(self):
        self.logger = logging.getLogger("security")
        handler = logging.FileHandler("security.log")
        handler.setFormatter(logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s'
        ))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def log_auth_event(
        self,
        event: str,
        user_id: str,
        ip_address: str,
        success: bool,
        details: str = "",
    ):
        """记录认证事件"""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event,
            "user_id": user_id,
            "ip_address": ip_address,
            "success": success,
            "details": details,
        }
        level = logging.INFO if success else logging.WARNING
        self.logger.log(level, json.dumps(log_entry))

    def log_data_access(self, user_id: str, document_id: str, action: str):
        """记录数据访问事件"""
        # 注意：不要记录文档内容！
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "data_access",
            "user_id": user_id,
            "document_id": document_id,
            "action": action,
        }
        self.logger.info(json.dumps(log_entry))


# ===== FastAPI 请求审计中间件 =====
class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # 记录请求
        security_logger = SecurityLogger()
        security_logger.log_auth_event(
            event="api_request",
            user_id=request.headers.get("X-User-ID", "anonymous"),
            ip_address=request.client.host if request.client else "unknown",
            success=True,
            details=f"{request.method} {request.url.path}",
        )

        response = await call_next(request)

        # 记录响应（不含 body）
        duration = time.time() - start_time
        response.headers["X-Response-Time"] = str(duration)

        return response
```

**错误示例**：
```python
# 🚫 错误：记录敏感信息到日志
logger.info(f"用户登录成功: {username}, 密码: {password}")  # 密码泄露！

# 🚫 错误：没有异常日志
try:
    result = process_payment()
except Exception:
    pass  # 什么也不记录，出了问题无法排查
```

---

### A10: Server-Side Request Forgery (SSRF)（服务端请求伪造）

**描述**：攻击者利用服务端功能发起内部网络请求，访问未授权的内部系统。

**影响**：
- 访问内部服务（如 127.0.0.1:6379—Redis）
- 内网探测
- 云服务元数据泄露（AWS IMDS）

**Python/FastAPI 防范示例**：

```python
from urllib.parse import urlparse
from typing import Set
import ipaddress
import socket
import requests as http_requests


class SSRFProtector:
    """SSRF 攻击防护"""

    # 禁止访问的内网网段
    BLOCKED_NETWORKS: Set[str] = {
        "127.0.0.0/8",       # 本地回环
        "10.0.0.0/8",        # 私有网络
        "172.16.0.0/12",     # 私有网络
        "192.168.0.0/16",    # 私有网络
        "169.254.0.0/16",    # 链路本地
        "0.0.0.0/8",         # 当前网络
        "::1/128",           # IPv6 本地回环
        "fc00::/7",          # IPv6 唯一本地地址
    }

    # AWS/GCP/Azure 元数据端点
    BLOCKED_HOSTS: Set[str] = {
        "169.254.169.254",   # AWS/GCP 元数据端点
        "metadata.google.internal",
        "100.100.100.200",   # 阿里云元数据
    }

    @classmethod
    def validate_url(cls, url: str) -> bool:
        """验证 URL 是否安全"""
        try:
            parsed = urlparse(url)
            hostname = parsed.hostname

            if not hostname:
                raise ValueError("无效 URL: 无主机名")

            # 检查黑名单主机
            if hostname in cls.BLOCKED_HOSTS:
                print(f"[BLOCKED] 禁止访问元数据端点: {hostname}")
                return False

            # 检查是否为 IP 地址
            try:
                ip = ipaddress.ip_address(hostname)
                for network in cls.BLOCKED_NETWORKS:
                    if ip in ipaddress.ip_network(network):
                        print(f"[BLOCKED] 禁止访问内网地址: {hostname} ({network})")
                        return False
            except ValueError:
                # hostname 是域名，需要 DNS 解析后再检查
                resolved = cls._resolve_and_check(hostname)
                if not resolved:
                    return False

            return True

        except Exception as e:
            print(f"[ERROR] URL 校验失败: {e}")
            return False

    @classmethod
    def _resolve_and_check(cls, hostname: str) -> bool:
        """DNS 解析后检查 IP 是否内网"""
        try:
            ips = socket.getaddrinfo(hostname, None)
            for addr in ips:
                ip = ipaddress.ip_address(addr[4][0])
                for network in cls.BLOCKED_NETWORKS:
                    if ip in ipaddress.ip_network(network):
                        print(f"[BLOCKED] DNS 解析到内网地址: {hostname} -> {ip}")
                        return False
            return True
        except socket.gaierror:
            print(f"[WARN] 无法解析域名: {hostname}")
            return False


# ===== 使用示例 =====
def safe_fetch_url(url: str) -> str:
    """安全的 URL 获取"""
    if not SSRFProtector.validate_url(url):
        raise ValueError("不安全的 URL 请求被拒绝")

    # 设置超时，防止 SSRF 横向利用
    response = http_requests.get(url, timeout=5)
    return response.text
```

**错误示例**：
```python
# 🚫 错误：直接转发用户 URL
@app.post("/api/v1/fetch")
async def fetch_url(url: str):
    response = requests.get(url)  # 用户可访问内网服务！
    return response.text

# 攻击者可访问:
# http://127.0.0.1:6379 (Redis)
# http://169.254.169.254/latest/meta-data/ (AWS 元数据)
```

---

## 工具链配置

```yaml
# 安全扫描 CI 配置（.github/workflows/security-scan.yml）
name: Security Scan
on:
  push:
    branches: [main, develop]
  pull_request:

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install dependencies
        run: pip install pip-audit safety bandit
      - name: Dependency scan
        run: |
          pip-audit --requirement requirements.txt
          safety check --file requirements.txt
      - name: Static analysis
        run: bandit -r app/ -f json -o bandit-report.json
```

```bash
# pre-commit 安全钩子（.pre-commit-config.yaml）
repos:
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.9
    hooks:
      - id: bandit
        args: ["-c", "pyproject.toml"]
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.0
    hooks:
      - id: gitleaks
```

---

## 参考来源

- OWASP Top 10 2021: https://owasp.org/www-project-top-ten/
- OWASP Cheat Sheet Series: https://cheatsheetseries.owasp.org/
- FastAPI Security: https://fastapi.tiangolo.com/tutorial/security/
- NIST SP 800-53 Rev. 5 (Access Control)
