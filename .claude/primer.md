# primer.md — 项目架构约定

> 最后更新: 2026-05-30
> 性质: 动态记忆层，随架构变更更新

## 项目身份

- **项目名称**：python-rag
- **技术栈**：Python 3.12+ / FastAPI / PostgreSQL + pgvector / Redis / LangChain 或 LlamaIndex
- **包管理器**：uv（禁止 pip）
- **代码检查**：Ruff（替代 Flake8 + isort）
- **类型检查**：mypy（strict 模式）
- **测试框架**：pytest + pytest-asyncio

## 架构决策记录

### ADR-001: 分层架构
- API 层（FastAPI 路由）→ Service 层（业务逻辑）→ Repository 层（数据访问）
- 所有外部依赖通过 FastAPI Depends 注入
- 每层定义抽象基类

### ADR-002: 向量数据库选型
- 主选：pgvector（与 PostgreSQL 统一运维）
- 备选：Milvus（大规模场景迁移）

### ADR-003: LLM 框架选型
- 首选 LangChain（生态成熟，社区大）
- 备选 LlamaIndex（数据索引场景更优）
- 通过抽象基类隔离框架差异

### ADR-004: 配置层级
- 4 层：L0 组织强制 → L1 用户全局 → L2 项目共享 → L3 项目本地
- L3 文件（settings.local.json / CLAUDE.local.md）git-ignored

### ADR-005: 记忆管理
- 静态层 CLAUDE.md → 动态层 primer.md + activeContext.md → 自动层 MEMORY.md
- 三钩防丢失：PreCompact / Stop / SessionStart
- 即时写入触发条件：决策 / bug修复 / 避坑 / 阶段完成 / PreCompact

## 关键约定

- 类型注解完整（mypy strict 零错误）
- docstring 齐全（Google 风格，中文）
- 单函数 ≤ 50 行，单类 ≤ 500 行
- 禁止裸 except、禁止 Any 类型、禁止循环中数据库查询
- 禁止 print() 调试，使用 structlog
