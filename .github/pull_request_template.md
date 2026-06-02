# Pull Request — 数学冒险世界

> **分支**: `{source}` → `{target}`
> **类型**: `feat / fix / refactor / test / docs / chore`

---

## 概述

<!-- 用 1-3 句话描述本次变更解决了什么问题。 -->

## 关联需求/架构

<!-- 关联 SRS 需求编号（如 REQ-DEC-001）或 ADR 编号（如 ADR-009）。无则填"无"。 -->

- **需求**: `REQ-XXX`
- **ADR**: `ADR-XXX`
- **安全影响**: `是 / 否`（若是，必须通过安全审查）

## 变更清单

<!-- 列出修改的文件和变更类型（新增/修改/删除）。 -->

| 文件 | 变更类型 | 说明 |
|------|---------|------|
| `src/...` | 新增/修改/删除 | ... |

## 质量门禁自检清单

### 代码风格与类型

- [ ] `ruff check src/` — 零警告
- [ ] `ruff format --check src/` — 格式合规
- [ ] `mypy --strict src/` — 零类型错误

### 测试

- [ ] `pytest --cov=src --cov-report=term --cov-fail-under=80` — 通过
- [ ] 新增代码有对应单元测试
- [ ] 核心决策引擎覆盖率 ≥ 90%

### 安全

- [ ] 未引入新的密钥/凭证硬编码
- [ ] 用户输入经过 Pydantic 校验（API 层）
- [ ] 无 SQL 拼接（全部使用 ORM 参数化查询）
- [ ] 日志中不包含敏感信息（密码/Token/PII）
- [ ] 新增依赖通过 `pip-audit` 安全扫描

### 架构规范

- [ ] 遵守分层架构（API → Service → Repository）
- [ ] 新增接口有 Pydantic schema 定义
- [ ] 函数 ≤ 50 行，类 ≤ 500 行
- [ ] 圈复杂度 ≤ 10
- [ ] 使用 structlog 而非 print()
- [ ] async 函数中无同步 I/O

### 文档与注释

- [ ] 公共函数/方法有 Google 风格 docstring（中文）
- [ ] 类型注解完整（mypy strict 无 `Any` 逃逸）
- [ ] 如有配置变更，已更新 `.env.example` 或相关文档

## 测试记录

<!-- 附上本地运行质量门禁的结果摘要。 -->

```
$ ruff check src/             → 0 errors
$ ruff format --check src/    → 0 files modified
$ mypy --strict src/          → Success
$ pytest --cov=src ...        → 100% passed, coverage xx%
$ pip-audit ...               → 0 vulnerabilities
```

## 部署注意事项

<!-- 是否需要数据库迁移？是否影响现有 API 兼容性？是否需要重启服务？ -->

- [ ] 需要数据库迁移（已附迁移脚本）
- [ ] API 向后兼容
- [ ] 需要 CI/CD 配置变更

---

**审查人请确认**：
- [ ] 代码逻辑正确性
- [ ] 异常路径已覆盖（空值、边界、网络错误、LLM 超时）
- [ ] 性能影响已评估（新增查询是否命中索引？是否引入 N+1？）
- [ ] 与非功能需求（SLA / 安全 / 合规）一致

> 本模板由 CLAUDE.md §质量门禁 自动生成
