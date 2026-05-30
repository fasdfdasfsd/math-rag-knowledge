---
category: Python生态链
priority: must
updated: 2026-05-30
---

# mypy 类型检查

## 概述

mypy 是 Python 静态类型检查工具，能在运行前发现类型相关的错误。本规范涵盖 Strict 模式配置、渐进式类型策略、常见类型注解模式以及 Any 类型的使用限制，帮助团队在类型安全与开发效率之间取得平衡。

## 核心规则

### 🔴 必须遵守 (MUST)

1. **所有函数必须包含类型注解**
   - 参数类型、返回值类型必须标注
   - 变量类型在无法推断时必须显式标注

2. **禁止在公开 API 中使用 `Any` 类型**
   - `Any` 会关闭类型检查，使其传递到调用链
   - 必须使用具体类型、`TypeVar` 或 `Protocol` 替代

3. **配置 Strict 模式**
   - 在 `pyproject.toml` 中启用 strict 模式
   - 或逐步启用核心选项：`warn_unused_configs`, `disallow_any_unimported`, `no_implicit_optional` 等

### 🟡 强烈建议 (SHOULD)

1. **渐进式类型策略**
   - 新代码必须 100% 有类型注解
   - 旧代码在修改时补充类型注解
   - 使用 `# type: ignore[code]` 处理第三方库缺类型，并附注原因

2. **常见模式**
   - 使用 `TypedDict` 定义字典结构
   - 使用 `Protocol` 定义接口协议
   - 使用 `Literal` 限制参数值范围
   - 使用 `Union` 和 `Optional` 处理可选值

3. **泛型使用**
   - 使用 `TypeVar` 定义泛型函数和类
   - 使用 `Generic` 定义泛型基类

### 🟢 可选建议 (MAY)

1. **运行时类型检查**
   - 使用 `isinstance()` 在边界处做防御性检查
   - Pydantic 模型自动提供运行时验证

2. **类型 stub 文件**
   - 为无类型注解的第三方库创建 `.pyi` 文件
   - 贡献上游类型注解

## 正确示例

```python
from typing import (
    List, Dict, Optional, Union, Any, TypeVar, Generic,
    Protocol, Literal, TypedDict, Sequence, Mapping,
    overload, assert_never,
)
from datetime import datetime
from pydantic import BaseModel


# ========== 基础类型注解 ==========

def greet(name: str, age: int = 18) -> str:
    """参数和返回值必须标注类型"""
    return f"Hello {name}, you are {age} years old."


def process_items(items: List[str]) -> Dict[str, int]:
    """复杂集合类型"""
    return {item: len(item) for item in items}


def find_user(user_id: int | None) -> Optional[dict]:
    """可选值"""
    if user_id is None:
        return None
    return {"id": user_id, "name": "Alice"}


# ========== TypedDict ==========

class UserDict(TypedDict):
    """TypedDict 定义字典结构"""
    id: int
    name: str
    email: str
    created_at: datetime


def create_user(data: UserDict) -> UserDict:
    """TypedDict 保证字典字段类型正确"""
    return {
        "id": data["id"],
        "name": data["name"],
        "email": data["email"],
        "created_at": data.get("created_at", datetime.now()),
    }


# ========== Protocol ==========

class Drawable(Protocol):
    """Protocol 定义接口协议 — 结构化子类型"""
    def draw(self) -> str:
        ...


class Circle:
    def draw(self) -> str:
        return "Drawing circle"


class Square:
    def draw(self) -> str:
        return "Drawing square"


def render(shape: Drawable) -> str:
    """接受任何实现了 Drawable protocol 的类型"""
    return shape.draw()


# ========== Literal ==========

HttpMethod = Literal["GET", "POST", "PUT", "DELETE", "PATCH"]


def make_request(url: str, method: HttpMethod = "GET") -> dict:
    """Literal 限制参数值范围"""
    return {"url": url, "method": method}


# 类型安全：
make_request("/api/users", "GET")     # 正确
make_request("/api/users", "DELETE")  # 正确
# make_request("/api/users", "INVALID")  # mypy 报错


# ========== TypeVar 泛型 ==========

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")


def first(items: List[T]) -> T | None:
    """泛型函数：返回列表第一个元素"""
    return items[0] if items else None


class Cache(Generic[K, V]):
    """泛型类：类型安全的缓存"""
    
    def __init__(self):
        self._store: dict[K, V] = {}
    
    def get(self, key: K) -> V | None:
        return self._store.get(key)
    
    def set(self, key: K, value: V) -> None:
        self._store[key] = value


# 使用泛型
cache: Cache[str, int] = Cache()
cache.set("count", 42)
value = cache.get("count")  # 类型为 int | None


# ========== overload ==========

@overload
def parse_input(data: str) -> dict:  # type: ignore[overload-overlap]
    ...

@overload
def parse_input(data: bytes) -> dict:
    ...

def parse_input(data: str | bytes) -> dict:
    """overload 处理不同类型参数"""
    if isinstance(data, bytes):
        return {"raw": data.hex()}
    return {"text": data}


# ========== Union 精确使用 ==========

class Success:
    def __init__(self, value: str):
        self.value = value

class Failure:
    def __init__(self, error: str):
        self.error = error

Result = Union[Success, Failure]


def handle_result(result: Result) -> str:
    """使用 Union 实现 discriminated union 模式"""
    match result:
        case Success(value):
            return f"Success: {value}"
        case Failure(error):
            return f"Failure: {error}"
        case _:
            assert_never(result)  # 确保所有情况都已处理


# ========== Pydantic 模型 ==========

class UserModel(BaseModel):
    id: int
    name: str
    email: str
    age: int | None = None


# ========== 受限制的 Any ==========

T_co = TypeVar("T_co", covariant=True)

class SafeContainer(Generic[T_co]):
    """避免使用 Any，使用类型变量"""
    def __init__(self, value: T_co):
        self._value = value
    
    def get(self) -> T_co:
        return self._value


# 不得已使用 Any 时，限制其传播范围
def legacy_interface(data: Any) -> str:
    """旧接口包装器：入口 Any，出口具体类型"""
    result = _process_legacy(data)  # type: ignore[no-untyped-call]
    return str(result)
```

## 错误示例

```python
# 错误 1：函数缺少类型注解

# 不推荐
def add(a, b):  # 参数和返回值都没有类型
    return a + b

# 推荐
def add(a: int, b: int) -> int:
    return a + b


# 错误 2：滥用 Any，关闭类型检查

def process(data: Any) -> Any:  # Any 污染调用链
    return data.unknown_method()  # mypy 不会报错


# 错误 3：隐式 Optional

# 不推荐
def find(id: int = None):  # type: ignore
    # mypy 要求显式 Optional
    pass

# 推荐
def find(id: int | None = None) -> dict | None:
    if id is None:
        return None
    return {"id": id}


# 错误 4：使用 dict 而非 TypedDict

def process_user(data: dict) -> dict:  # 字典内容不明确
    return {
        "name": data.get("name", ""),  # data["name"] 可能不存在
        "email": data["email"],  # 类型未知
    }

# 应定义 UserDict


# 错误 5：忽略类型错误

def divide(a: int, b: int) -> float:
    return a / b

result = divide("10", 0)  # type: ignore  # 错误：不应忽略
# 应使用正确类型


# 错误 6：过度使用 Union

# 不推荐
def handle(value: Union[str, int, float, bool, None, List[str]]):
    # 太多类型说明设计有问题
    pass

# 推荐：拆分为多个重载或使用 Protocol


# 错误 7：没有处理 None

def get_length(items: List[int] | None) -> int:
    return len(items)  # mypy 报错：items 可能为 None

# 正确
def get_length(items: List[int] | None) -> int:
    if items is None:
        return 0
    return len(items)
```

## 工具链配置

```toml
# pyproject.toml — mypy 配置
[tool.mypy]
# Strict 模式等效选项
strict = true

# 或逐步启用：
# disallow_any_unimported = true
# disallow_any_expr = false
# disallow_any_decorated = false
# disallow_any_explicit = true
# disallow_any_generics = true
# disallow_subclassing_any = true
# disallow_untyped_calls = true
# disallow_untyped_defs = true
# disallow_incomplete_defs = true
# check_untyped_defs = true
# disallow_untyped_decorators = true
# no_implicit_optional = true
# warn_redundant_casts = true
# warn_unused_ignores = true
# warn_return_any = true
# warn_unreachable = true

# 排除
exclude = [
    ".venv",
    "build",
    "migrations",
    "tests/",
]

# 模块级忽略
[[tool.mypy.overrides]]
module = ["tests.*"]
disallow_untyped_defs = false  # 测试文件可以放宽

[[tool.mypy.overrides]]
module = ["migrations.*"]
ignore_errors = true
```

运行命令：

```bash
# 检查所有文件
mypy src

# 检查特定模块
mypy src/myproject/user

# 显示错误代码
mypy --show-error-codes src

# 严格模式
mypy --strict src

# 增量模式（快）
mypy --no-incremental src

# 输出统计
mypy --stats src
```

## 参考来源

- [mypy 官方文档](https://mypy.readthedocs.io/)
- [Python typing 模块文档](https://docs.python.org/3/library/typing.html)
- [PEP 484 — Type Hints](https://peps.python.org/pep-0484/)
