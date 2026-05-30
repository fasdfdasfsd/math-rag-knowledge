# L2 — 项目共享层

> 部署位置：`<项目根>/` 和 `<项目根>/.claude/`

## 包含文件

| 文件 | 部署位置 | 说明 |
|------|----------|------|
| `CLAUDE.md` | `./CLAUDE.md` | 项目指令 + 推理质量纪律 + 子代理策略 + 记忆管理 |
| `settings.json` | `./.claude/settings.json` | 9 Hooks + 24 权限规则 |
| `.claudeignore` | `./.claudeignore` | Token 优化排除规则 |
| `.claude/rules/*.md` | `./.claude/rules/` | 路径作用域规则（5 个） |
| `primer.md` | `./.claude/primer.md` | 架构决策记录 (ADR) |
| `activeContext.md` | `./.claude/activeContext.md` | 当前任务状态 |
| `MEMORY.md` | `./.claude/MEMORY.md` | 会话记忆 |
| `global-memory.md` | `~/.claude/projects/.../memory/` | 全局记忆模板 |
| `../knowledge/` | `./knowledge/` | 规范文件（82 个）+ 管理文档（8 个） |

## 知识体系

### knowledge/（规范文档 — 详尽指南）

```
knowledge/
├── 01~10/（82 个规范文件）
├── 知识文件模板规范.md
├── 规则强制执行映射表.md
├── 知识反馈闭环协议.md
├── 知识审查协议.md
└── 避坑汇总.md
```

### .claude/rules/（路径规则 — 自动注入）

| 文件 | paths | 触发时机 |
|------|-------|----------|
| `python.md` | `src/**/*.py`, `tests/**/*.py` | 编辑 Python 文件 |
| `api.md` | `src/api/**/*.py` | 编辑 API 路由 |
| `database.md` | `src/repositories/**/*.py` | 编辑数据访问层 |
| `security.md` | 全局（无 paths） | 始终生效 |
| `testing.md` | `tests/**/*.py` | 编辑测试文件 |

**规则加载机制**：
- 无 `paths` 字段 → 会话启动时加载
- 有 `paths` 字段 → Claude 接触匹配文件时自动注入
- Token 高效：不碰 `src/api/` 时 `api.md` 不占用上下文

## 知识反馈闭环

```
避坑（MEMORY.md）→ SessionStart 提醒 → 归入避坑汇总 → 固化到规范/规则 → 季度审查
```

## 部署步骤

```bash
# 1. CLAUDE.md + .claudeignore
cp config/L2-项目共享/CLAUDE.md ./CLAUDE.md
# .claudeignore 已在项目中

# 2. .claude/ 配置
mkdir -p .claude .claude/rules
cp config/L2-项目共享/settings.json .claude/settings.json
cp config/L2-项目共享/primer.md .claude/primer.md
cp config/L2-项目共享/activeContext.md .claude/activeContext.md
cp config/L2-项目共享/MEMORY.md .claude/MEMORY.md

# 3. .claude/rules/ 已在项目中（Git 版本控制），无需额外部署
# 4. knowledge/ 已在项目中（Git 版本控制），无需额外部署
# 5. 全局记忆目录
mkdir -p ~/.claude/projects/D--panzt-projects-claude-code-python-rag/memory/
```

## 验证

重启 Claude Code，应看到：
```
═══ 记忆文件状态 ═══
✅ .claude/MEMORY.md
✅ .claude/primer.md
✅ .claude/activeContext.md
✅ CLAUDE.md

═══ 项目健康检查 ═══
📅 上次退出: ...
🧪 测试: ...
📝 避坑: ...
══════════════════
```

验证路径规则自动注入：
```
# 编辑 src/api/ 下的文件 → api.md 规则自动生效
# 编辑 tests/ 下的文件 → testing.md 规则自动生效
```
