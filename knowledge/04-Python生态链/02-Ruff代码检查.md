---
category: Python生态链
priority: must
updated: 2026-05-30
---

# Ruff 代码检查

## 概述

Ruff 是 Astral 公司开发的极速 Python 代码检查工具，用 Rust 编写，比传统 Flake8 快 10-100 倍。Ruff 内置了超过 700 条 lint 规则，覆盖 Flake8、isort、pyupgrade 等功能，是 Python 项目的推荐代码检查工具。

## 核心规则

### 🔴 必须遵守 (MUST)

1. **所有提交的代码必须通过 Ruff 检查**
   - 禁止合入有任何 Ruff 警告的代码
   - CI 流程中必须包含 Ruff 检查步骤

2. **项目必须配置一致的 Ruff 规则集**
   - 在 `pyproject.toml` 中声明规则
   - 团队所有成员使用相同配置

3. **使用 `ruff check --fix` 自动修复**
   - 常规 lint 问题优先使用自动修复
   - 提交前运行 fix

### 🟡 强烈建议 (SHOULD)

1. **已启用的规则集说明**
   - **E/W**：Flake8 错误/警告（基础代码质量）
   - **F**：Pyflakes 规则（逻辑错误检测）
   - **I**：isort 规则（导入顺序）
   - **N**：PEP8 命名规范
   - **B**：bugbear 规则（常见 bug 检测）
   - **C4**：comprehensions（推导式优化）
   - **UP**：pyupgrade（Python 版本升级语法）
   - **ARG**：未使用的参数检测
   - **SIM**：代码简化建议
   - **TCH**：类型检查导入优化

2. **VS Code 集成**
   - 安装 Ruff 扩展
   - 配置保存时自动格式化

3. **排除规则**
   - 对特定文件/目录可以排除特定规则
   - 需在配置中显式声明并注明原因

### 🟢 可选建议 (MAY)

1. **自定义规则**
   - 使用 `ruff.lint.extend-safe-fixes` 扩展安全修复
   - 针对项目特有约定添加规则

2. **预提交钩子**
   - 配置 pre-commit hook 自动运行 Ruff

## 正确示例

```toml
# pyproject.toml — Ruff 完整配置
[tool.ruff]
# 目标 Python 版本
target-version = "py311"

# 检查的文件
include = ["*.py", "*.pyi"]

# 排除的目录
exclude = [
    ".venv",
    ".git",
    "__pycache__",
    "migrations",
    "build",
    "dist",
]

# line-length
line-length = 100

# 缩进
indent-width = 4

# 启用规则集
[tool.ruff.lint]
select = [
    "E",    # pycodestyle 错误
    "W",    # pycodestyle 警告
    "F",    # Pyflakes
    "I",    # isort
    "N",    # PEP8 命名
    "B",    # bugbear
    "C4",   # comprehensions
    "UP",   # pyupgrade
    "ARG",  # 未使用的参数
    "SIM",  # 代码简化
    "TCH",  # type-checking
]

# 忽略的规则
ignore = [
    "E501",   # 行长度（由 formatter 处理）
    "N818",   # 异常命名后缀
]

# 每个文件允许的未修复警告数
per-file-ignores = {
    "__init__.py": ["F401"],  # __init__.py 中允许未使用的 import
    "tests/*.py": ["ARG001"], # 测试文件中允许未使用的参数
    "scripts/*.py": ["TCH001"], # 脚本中允许运行时的类型导入
}

# isort 配置
[tool.ruff.lint.isort]
known-first-party = ["myproject"]
known-third-party = ["fastapi", "pydantic", "sqlalchemy"]
force-single-line = false

# 命名规范
[tool.ruff.lint.pep8-naming]
classmethod-decorators = ["classmethod", "pydantic.validator"]

# 代码格式化
[tool.ruff.format]
quote-style = "double"
indent-style = "space"
line-ending = "auto"
```

运行命令：

```bash
# 检查所有文件
ruff check .

# 自动修复
ruff check --fix .

# 仅检查暂存区文件
ruff check --staged .

# 格式化代码
ruff format .

# CI 模式（失败时返回非零退出码）
ruff check --exit-non-zero-on-fix .
```

## 错误示例

```python
# 以下代码会触发 Ruff 警告

# 错误 1：未使用的导入 (F401)
import os     # 未使用
import json  # 未使用


# 错误 2：导入顺序不正确 (I001)
# isort 要求：标准库 → 第三方 → 本地
from myproject.models import User  # 本地库应放在最后
import fastapi  # 第三方库应放在中间
import os       # 标准库应放在最前


# 错误 3：PEP8 命名规范 (N801, N802, N803)
class myclass:  # 应改为 MyClass
    def MyMethod(self):  # 应改为 my_method
        pass


# 错误 4：未使用的函数参数 (ARG001)
def process(data, unused_param):  # unused_param 未使用
    return data * 2


# 错误 5：可简化的推导式 (C400)
# 不推荐
result = [x for x in range(10)]  # 应改为 list(range(10))


# 错误 6：未使用的变量 (F841)
def compute():
    temp = calculate()  # 定义后未使用
    return 42


# 错误 7：类型比较 (E721)
def check(value):
    if type(value) == int:  # 应使用 isinstance(value, int)
        return True
    return False
```

## 错误示例（提交）

```bash
# 错误操作：提交前不运行 Ruff

# 开发者在本地修改了代码
# 没有运行 ruff check 就提交
git add .
git commit -m "feat: add new feature"

# CI 检查时发现大量 Ruff 警告
# 构建失败，需要回退重改


# 错误操作：忽略 Ruff 警告强行提交
git commit --no-verify -m "紧急修复：绕过 lint 检查"
# 长期来看代码质量下降，积累技术债务
```

## 工具链配置

```bash
# VS Code settings.json
"""
{
    "[python]": {
        "editor.formatOnSave": true,
        "editor.defaultFormatter": "charliermarsh.ruff",
        "editor.codeActionsOnSave": {
            "source.fixAll": "explicit",
            "source.organizeImports": "explicit"
        }
    },
    "ruff.lint.run": "onType",
    "ruff.organizeImports": true
}
"""

# pre-commit 配置 (.pre-commit-config.yaml)
"""
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
"""
```

## 参考来源

- [Ruff 官方文档](https://docs.astral.sh/ruff/)
- [Ruff 规则列表](https://docs.astral.sh/ruff/rules/)
- [Ruff VS Code 扩展](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff)
