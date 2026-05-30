---
category: 05-编程语言规范
priority: must
updated: 2026-05-30
---

# Python PEP8 与编码规范

## 概述

本文档定义 Python 项目的编码规范基线，以 PEP 8 (Style Guide for Python Code) 为核心，融合 PEP 20 (Zen of Python)、PEP 257 (Docstring Conventions) 和 PEP 484 (Type Hints) 的要求，并明确自动化工具（Ruff、Black）的配置标准。所有 Python 代码必须通过 Ruff 静态检查，格式由 Black 或 Ruff Format 统一。

## 核心规则

### MUST（强制遵守）

#### 缩进与格式

- **缩进**：使用 4 个空格，禁止使用 Tab。
- **行长**：最大行长度 120 字符（PEP 8 原标准为 79，团队经评估放宽至 120）。
- **换行**：推荐使用圆括号隐式续行，避免使用反斜杠 `\` 续行。
- **空行**：
  - 顶层函数和类定义前后各空 2 行。
  - 类内部方法定义之间空 1 行。
  - 函数内逻辑段落之间可空 1 行。
- **文件末尾**：保留一个空行。

#### import 顺序

严格按以下三组分组，每组间空一行，组内按字母序排列：

1. Python 标准库（`os`, `sys`, `json` 等）
2. 第三方库（`fastapi`, `numpy`, `asyncpg` 等）
3. 本地模块（当前项目的包内引用）

禁止使用 `from module import *`。

#### 命名规范

| 元素 | 命名风格 | 示例 |
|------|----------|------|
| 变量 / 函数 / 方法 | snake_case | `user_name`, `get_user()` |
| 类 | PascalCase | `UserProfile`, `DatabaseManager` |
| 常量 | UPPER_CASE | `MAX_RETRY_COUNT`, `DEFAULT_TIMEOUT` |
| 私有属性/方法 | 前导单下划线 | `_internal_cache` |
| 名称重整（避免子类冲突） | 前导双下划线 | `__private_method` |
| 模块名 | 简短 snake_case | `utils`, `db_connection` |
| 包名 | 简短 snake_case（不建议用下划线） | `rag_core`, `api` |

#### 类型注解（PEP 484）

- 所有函数参数和返回值必须标注类型。
- 变量声明在复杂类型时建议标注。
- 使用 `typing` 模块或 Python 3.10+ 的 `|` 联合类型语法。

```python
from typing import Optional


def process_item(item_id: str, timeout: float = 30.0) -> dict[str, Any]:
    ...
```

#### Docstring（PEP 257）

- 所有公开模块、函数、类、方法必须有 docstring。
- 使用三重双引号 `"""docstring"""`。
- 单行 docstring 首尾引号同行。
- 多行 docstring：首行概述，空行后跟详细说明，末尾引号单独一行。
- 推荐使用 Google Style 或 NumPy Style 格式。

### SHOULD（建议遵守）

- 每行只写一个赋值/语句。
- 比较操作使用 `is` / `is not` 判断 `None`，而非 `==`。
- 布尔值判断使用 `if x:` / `if not x:` ，而非 `if x is True:`。
- 列表/字典/集合推导式可读性良好时优先使用。
- 优先使用 Pathlib 而非 `os.path` 处理文件路径。
- 优先使用 f-string 而非 `%` 格式化或 `str.format()`。

### MAY（可选的推荐）

- 可以忽略行长限制的情况：URL 字符串、长路径、pytest 装饰器参数过长。
- 函数参数较多时（超过 5 个），可以考虑使用 `dataclass` 或 `TypedDict` 整合。

## 正确示例

```python
"""Core user management module.

This module provides user CRUD operations with PostgreSQL backend.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime
from typing import Any

import asyncpg
from pydantic import BaseModel

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)
MAX_LOGIN_ATTEMPTS = 5


class UserProfile(BaseModel):
    """Representation of a user profile.

    Attributes:
        user_id: Unique identifier (UUID v4).
        email: User email address.
        display_name: Optional public display name.
        created_at: Account creation timestamp.
    """

    user_id: str
    email: str
    display_name: str | None = None
    created_at: datetime


async def get_user_by_email(
    pool: asyncpg.Pool,
    email: str,
) -> UserProfile | None:
    """Retrieve a user profile by email address.

    Args:
        pool: Database connection pool.
        email: Target email address.

    Returns:
        UserProfile instance if found, None otherwise.
    """
    query = "SELECT user_id, email, display_name, created_at FROM users WHERE email = $1"
    row = await pool.fetchrow(query, email)
    if row is None:
        logger.info("User not found: %s", email)
        return None
    return UserProfile(**dict(row))
```

## 错误示例

```python
# 错误 1：混合缩进（Tab + 空格）
def foo():
	first_name = "Alice"  # Tab 缩进
    last_name = "Bob"     # 空格缩进 → 报语法错误

# 错误 2：行长超过限制且硬换行
result = some_long_function_name(argument_one, argument_two, argument_three, argument_four, argument_five, argument_six)  # 超过 120 字符

# 错误 3：import 顺序混乱、使用 *
import os
from fastapi import *
import sys
from .models import User
import json

# 错误 4：命名不规范
class user_profile:        # 类应该用 PascalCase
    def GetFullName(self):  # 方法应该用 snake_case
        pass

MAX_COUNT = 100             # 这应该是常量（大写），但如果只是模块级变量请用小写

# 错误 5：缺少类型注解
def calculate(x, y):        # 缺少参数和返回类型
    return x + y

# 错误 6：docstring 格式错误
def add(a, b):
    'add two numbers'       # 应该用双引号三重引号
    return a + b

# 错误 7：使用反斜杠续行
if very_long_condition_1 and very_long_condition_2 and \
   very_long_condition_3 and very_long_condition_4:
    do_something()

# 正确写法：使用括号隐式续行
if (
    very_long_condition_1
    and very_long_condition_2
    and very_long_condition_3
    and very_long_condition_4
):
    do_something()

# 错误 8：用 == 比较 None
if result == None:
    pass
# 正确写法：
if result is None:
    pass
```

## 工具链配置

### Ruff（首选 Linter & Formatter）

`pyproject.toml` 配置：

```toml
[tool.ruff]
target-version = "py311"
line-length = 120

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "D", "B", "SIM", "UP", "ANN"]

[tool.ruff.lint.pydocstyle]
convention = "google"

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
docstring-code-format = true
```

### Black（备选 Formatter）

`pyproject.toml` 配置：

```toml
[tool.black]
line-length = 120
target-version = ["py311"]
skip-magic-trailing-comma = true
```

### mypy（类型检查）

`pyproject.toml` 配置：

```toml
[tool.mypy]
python_version = "3.11"
strict = true
ignore_missing_imports = true
disallow_untyped_defs = true
```

## 参考来源

- [PEP 8 – Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [PEP 20 – The Zen of Python](https://peps.python.org/pep-0020/)
- [PEP 257 – Docstring Conventions](https://peps.python.org/pep-0257/)
- [PEP 484 – Type Hints](https://peps.python.org/pep-0484/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Black Documentation](https://black.readthedocs.io/)
- Google Python Style Guide
