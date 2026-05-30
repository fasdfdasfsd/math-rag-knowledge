---
category: Python生态链
priority: must
updated: 2026-05-30
---

# pytest 测试框架

## 概述

pytest 是 Python 最流行的测试框架，支持简单的单元测试到复杂的功能测试。本规范涵盖测试结构组织、Fixtures 使用模式、异步测试、Mock 策略、参数化测试及覆盖率要求。

## 核心规则

### 🔴 必须遵守 (MUST)

1. **测试文件结构镜像 src/ 目录**
   - `src/myproject/module.py` → `tests/test_module.py`
   - `src/myproject/subpkg/module.py` → `tests/subpkg/test_module.py`

2. **代码行覆盖率必须 ≥ 80%**
   - 核心业务逻辑模块覆盖率目标 ≥ 90%
   - 新增代码必须附带测试

3. **测试函数命名必须规范**
   - 格式：`test_{function_name}_{scenario}_{expected_result}`
   - 示例：`test_create_user_with_valid_email_returns_user_object`

### 🟡 强烈建议 (SHOULD)

1. **Fixtures 使用模式**
   - 使用 conftest.py 共享 fixtures
   - fixture scope 合理设置：session > module > class > function
   - 避免在 fixture 中执行过多的 setup 操作

2. **异步测试**
   - 使用 `pytest-asyncio` 插件
   - 测试异步函数时添加 `@pytest.mark.asyncio`

3. **Mock 策略**
   - 优先使用 `pytest-mock`（返回 `mocker` fixture）
   - 只 Mock 外部依赖，不 Mock 被测试模块内部的函数
   - 验证 Mock 调用次数和参数

### 🟢 可选建议 (MAY)

1. **参数化测试**
   - 对边界值和错误路径使用参数化
   - 使用 `pytest.mark.parametrize`

2. **快照测试**
   - 使用 `syrupy` 做快照测试
   - 适用于 API 响应、复杂数据结构

## 正确示例

```python
# ========== 目录结构 ==========
"""
my-project/
  src/
    myproject/
      __init__.py
      user/
        __init__.py
        service.py
        repository.py
        models.py
  tests/
    __init__.py
    conftest.py          # 全局 fixtures
    user/
      __init__.py
      conftest.py        # user 模块 fixtures
      test_service.py
      test_repository.py
"""


# ========== conftest.py — 共享 Fixtures ==========

# tests/conftest.py
import pytest
from typing import AsyncGenerator
from unittest.mock import AsyncMock


@pytest.fixture(scope="session")
def db_url() -> str:
    """测试数据库连接 URL（session 级别）"""
    return "postgresql://test:test@localhost:5432/testdb"


@pytest.fixture
def mock_db_session(mocker):
    """Mock 数据库 session（函数级别）"""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


# tests/user/conftest.py
@pytest.fixture
def user_service(mock_db_session):
    """用户服务实例"""
    from myproject.user.service import UserService
    from myproject.user.repository import UserRepository
    
    repo = UserRepository(db_session=mock_db_session)
    service = UserService(repository=repo)
    return service


# ========== 测试文件：test_service.py ==========

import pytest
from datetime import datetime


# 基本测试
def test_create_user_with_valid_email_returns_user(user_service, mock_db_session):
    """测试：有效 email 创建用户返回用户对象"""
    from myproject.user.models import UserCreate
    
    # Arrange
    user_data = UserCreate(
        email="test@example.com",
        username="testuser",
        password="SecurePass123!",
    )
    mock_db_session.execute.return_value.scalar_one_or_none.return_value = None
    
    # Act
    result = user_service.create_user(user_data)
    
    # Assert
    assert result is not None
    assert result.email == "test@example.com"
    assert result.username == "testuser"
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()


# 参数化测试
@pytest.mark.parametrize(
    "email,expected_valid",
    [
        ("user@example.com", True),
        ("user+tag@example.com", True),
        ("user@sub.example.com", True),
        ("not-an-email", False),
        ("@example.com", False),
        ("user@", False),
        ("", False),
        (None, False),
    ],
)
def test_email_validation(email, expected_valid, user_service):
    """测试：多种 email 格式的验证"""
    result = user_service.validate_email(email)
    assert result == expected_valid


# 异常路径测试
def test_create_user_with_duplicate_email_raises_error(user_service, mock_db_session):
    """测试：重复 email 抛出异常"""
    from myproject.user.models import UserCreate
    from myproject.user.exceptions import DuplicateEmailError
    
    user_data = UserCreate(
        email="existing@example.com",
        username="newuser",
        password="SecurePass123!",
    )
    mock_db_session.execute.return_value.scalar_one_or_none.return_value = {
        "id": 1, "email": "existing@example.com"
    }
    
    with pytest.raises(DuplicateEmailError):
        user_service.create_user(user_data)


# 异步测试
@pytest.mark.asyncio
async def test_async_search_users(user_service, mock_db_session):
    """测试：异步搜索用户"""
    mock_result = [
        {"id": 1, "username": "alice", "email": "alice@example.com"},
        {"id": 2, "username": "bob", "email": "bob@example.com"},
    ]
    mock_db_session.execute.return_value.fetchall.return_value = mock_result
    
    results = await user_service.search_users_async("a")
    
    assert len(results) == 2
    assert results[0]["username"] == "alice"


# Mock 外部依赖
def test_send_welcome_email(mocker, user_service):
    """测试：注册成功后发送欢迎邮件"""
    from myproject.notifications import email_service
    
    # Mock 邮件服务
    mock_send = mocker.patch.object(email_service, "send_email", return_value=True)
    
    user_service.create_user({
        "email": "new@example.com",
        "username": "newuser",
    })
    
    # 验证邮件发送
    mock_send.assert_called_once()
    call_args = mock_send.call_args[0]
    assert "new@example.com" in call_args
    assert "Welcome" in call_args[1]


# Fixture 清理
@pytest.fixture
def temp_file(tmp_path):
    """临时文件 fixture，自动清理"""
    file_path = tmp_path / "test.txt"
    file_path.write_text("test data")
    yield file_path
    # teardown：tmp_path 自动清理


def test_file_processing(temp_file):
    """测试：文件处理"""
    from myproject.utils import process_file
    result = process_file(str(temp_file))
    assert result == "PROCESSED: test data"
```

## 错误示例

```python
# 错误 1：测试命名不规范

def test_1():  # 无意义命名
    pass

def test_user():  # 不描述场景
    pass

def test_a():  # 无信息量
    pass


# 错误 2：测试没有断言

def test_create_user(user_service):
    """测试创建用户"""
    result = user_service.create_user({"email": "test@test.com"})
    # 没有断言！测试通过了也没验证任何东西


# 错误 3：测试依赖顺序

# test_users.py
users = []  # 全局状态

def test_create():
    users.append("user1")  # 依赖全局状态
    assert len(users) == 1

def test_delete():
    # 依赖 test_create 先执行
    users.pop()
    assert len(users) == 0

# 测试执行顺序不可靠！应每个测试独立


# 错误 4：Mock 了整个实现而非外部依赖

def test_user_service_bad(mocker):
    """Mock 了被测试模块的内部方法"""
    from myproject.user.service import UserService
    
    service = UserService()
    # 错误：Mock 内部方法
    service._validate = mocker.Mock(return_value=True)
    service._save_to_db = mocker.Mock(return_value={"id": 1})
    
    result = service.create_user(...)
    # 等于什么都没测！


# 错误 5：异步测试没有标记

def test_async_function():
    """异步测试缺少 @pytest.mark.asyncio"""
    result = await some_async_function()  # SyntaxError!
    assert result == expected


# 错误 6：覆盖率和断言不足

def test_complex_business_logic(user_service):
    """只测试了正常路径"""
    result = user_service.process_order(...)
    assert result is not None  # 太弱
    # 没有检查：
    # - 金额计算是否正确
    # - 库存是否扣减
    # - 订单状态是否正确
    # - 异常路径处理
```

## 工具链配置

```toml
# pyproject.toml — pytest 配置
[tool.pytest.ini_options]
minversion = "8.0"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]

# 异步测试配置
asyncio_mode = "auto"

# 标记注册
markers = [
    "slow: 慢速测试（集成测试）",
    "network: 依赖网络连接的测试",
    "smoke: 冒烟测试",
]

# 覆盖率配置
[tool.coverage.run]
source = ["src"]
omit = [
    "*/migrations/*",
    "*/tests/*",
    "*/__init__.py",
]

[tool.coverage.report]
show_missing = true
fail_under = 80
skip_empty = true
```

运行命令：

```bash
# 运行所有测试
pytest

# 运行特定文件
pytest tests/user/test_service.py

# 运行特定测试函数
pytest tests/user/test_service.py::test_email_validation

# 运行带标记的测试
pytest -m slow

# 带覆盖率运行
pytest --cov=src --cov-report=term-missing

# 并行运行
pytest -n auto

# 失败时停止
pytest -x

# 详细输出
pytest -v
```

## 参考来源

- [pytest 官方文档](https://docs.pytest.org/)
- [pytest-asyncio 文档](https://pytest-asyncio.readthedocs.io/)
- [pytest-cov 文档](https://pytest-cov.readthedocs.io/)
