---
name: session-2026-06-01-final
description: 2026-06-01 全天会话 — 阶段 0-10 全部完成，项目交付就绪
metadata:
  type: session_memory
  session_date: 2026-06-01
---

# 会话记忆 — 2026-06-01（最终状态）

## 整体进度

- **11 阶段流程**：阶段 0-10 全部完成 ✅
- **整体进度**：100%（按阶段加权）
- **16 次多智能体部署**（7 批次）
- **22 份设计文档**

## 代码产出

| 层级 | 文件数 | 状态 |
|------|--------|------|
| 后端 Python | 52 个 | mypy strict 零错误 |
| 前端 TypeScript/TSX | 25 个 | TypeScript 零错误 |
| 测试 | 239 个 | 229 unit + 10 integration |
| 基础设施 | Docker 5/6 healthy | PG+Redis+Milvus 正常 |

## 关键架构决策（ADR）

见 `.claude/primer.md` — ADR-001 至 ADR-015 + ADR-SEC-001 至 SEC-006

核心决策：
- 三层解耦架构（Decision Engine → RAG → LLM）
- 模块化单体（非微服务）
- PostgreSQL 关系表存知识图谱
- LLMProvider ABC + 工厂模式（运行时热切换）
- 段落级 SSE 流式推送
- Pre/Post-LLM 双端内容安全审核

## 避坑记录

1. **DEEPSEEK_BASE_URL 双 /v1**：配置默认值 `https://api.deepseek.com/v1` 但 OpenAI SDK 自动追加 `/v1`，导致 404。修正为 `https://api.deepseek.com`。`.env` 需手动修改或使用启动脚本覆盖。
2. **passlib 与 bcrypt≥4.1 不兼容**：passlib 依赖 `bcrypt.__about__` 属性（bcrypt 4.1+ 已移除）。迁移到原生 bcrypt API。
3. **EventSource 不支持自定义 Header**：SSE 认证改用 fetch + ReadableStream 手动解析。
4. **Docker 镜像仓库全部不可用**：通过缓存镜像版本标记绕过。
5. **上下文溢出**：达到 567k/200k（283%），加强上下文监控规则并写入 CLAUDE.md。

## 唯一阻塞项

- `.env` 文件 `DEEPSEEK_BASE_URL` 需从 `https://api.deepseek.com/v1` 改为 `https://api.deepseek.com`（去掉 `/v1`）
- 启动脚本 `scripts/dev.ps1` 和 `scripts/start-dev.sh` 已自动覆盖此变量

## 产品治理红线

- `docs/产品治理规则-数学冒险世界-v1.md` — 70+ 条规则，6 大领域
- 4 层执行：Pre-LLM 消毒 → System Prompt 硬约束 → Post-LLM 审核 → 人工抽检
- 3 级管控：🔴 代码阻断 / 🟡 Post-LLM 验证 / 🟢 人工抽检

## 上下文监控规则（已写入 CLAUDE.md）

- R1: ≥75% 警告
- R2: ≥100% 立即 compact
- R3: ≥200% 保存恢复点 + compact（丢失关键信息视为事故）
- 每次回复前自检

## 行为宪法（2026-06-02 落定）

用户反复强调的核心要求已写入三层配置，每次会话自动加载：

| 文件 | 层级 | 内容 |
|------|------|------|
| `.claude/rules/behavior.md` | 项目规则 | 4 条红线：决策协议/无人值守/上下文监控/共识优先 |
| `.claude/rules/autonomous.md` | 项目规则 | 禁止词汇表 + 替代表达 + 执行节奏 |
| `CLAUDE.md` 顶部引用 | 项目指令 | 启动即见的行为宪法链接 |
| `~/.claude/CLAUDE.md` 顶部引用 | 全局指令 | 所有项目生效的决策+值守+监控规则 |
| `.claude/settings.json` SessionStart | Hook | 启动时打印行为宪法摘要 |

**这些规则现在已固化到配置文件中，下次打开 Claude Code 自动生效。**

## 下次会话启动

```bash
# 启动后端
uv run uvicorn src.main:app --port 8000 --reload

# 启动前端（另一个终端）
cd frontend && npm run dev

# 或一键启动
.\scripts\dev.ps1   # Windows
bash scripts/start-dev.sh  # Unix
```
