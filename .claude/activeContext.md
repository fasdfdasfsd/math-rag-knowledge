# activeContext — 会话恢复点

> 最后更新: 2026-06-02 上午 | 会话状态: 进行中

## 本次会话变更（2026-06-02）

### 环境配置强化
- **D-016**: 知识库强制执行 + 修订权限管制 + 输入预处理协议 | 三文件同步更新
  - `CLAUDE.md`：新增知识库强制执行（K-1~K-4）+ 管家职责"知识库治理"+ 输入预处理协议 + 知识库修订 SOP（9步）
  - `.claude/rules/behavior.md`：新增第七条（知识库修订权限管制）+ 第八条（输入预处理协议）
  - `.claude/rules/autonomous.md`：执行节奏新增第1步"输入预处理"

### 新规则摘要
| 规则 | 核心 |
|------|------|
| 知识库强制执行 | knowledge/ 优先于一切，冲突时以 knowledge/ 为准 |
| 知识库修订 | 仅管家派遣 KB-Editor 子智能体 → ≥2 权威来源 → ≥2 审查 → ADR |
| 输入预处理 | 理解→分析→调度→反馈→执行（分级：简单=轻量，中等+=四板块） |
| 合规审计 CmplAud | 三域自动化合规验证（环境/知识库/用户输入）→ 🔴阻断 🟡警告 🟢记录 |

### 合规审计子智能体（2026-06-02 第二轮）
- **D-018**: 创建 CmplAud（合规审计员）| 独立审计角色，全阶段常驻 | 依据：用户需求"专职子智能体负责全程检查/监督/审批"
  - 角色：🛡️ CmplAud（RASCI: C — 全阶段咨询）
  - 三域：环境配置（ENV）/ 本地知识库（KB）/ 用户输入（INPUT）
  - 双模式：常驻快检（flash，每轮自动）+ 深度审计（pro，阶段准出/知识库变更/会话结束）
  - 核心原则：安全带模式（自动锁止），非收费站（人工审批）——与无人值守完全兼容
  - 管家覆盖权：🔴 阻断可覆盖但须记录 ADR
  - 新增文件：`.claude/rules/compliance.md`（~120 项详细检查清单）
  - 行为宪法更新：behavior.md 第九条

## 项目状态

## 项目状态

- **阶段**: 0-10 全部完成（11/11 = 100%）
- **后端**: 52 个 Python 文件，mypy strict 零错误
- **前端**: 25 个 TS/TSX 文件，TypeScript 零错误，Vite build 191ms
- **测试**: 275 个全部通过，覆盖率 91%（+36 个新增，+6%）
- **Docker**: 6/6 healthy ✅（content-validation 独立轻量应用部署成功）
- **前端**: TypeScript 零错误，Vite build 408ms，PWA（离线缓存 + Push Notification）已交付
- **DeepSeek E2E**: 已验证通过

## 前后端联通

- 后端: `uv run uvicorn src.main:app --port 8000 --reload`
- 前端: `cd frontend && npm run dev`（http://localhost:5173）
- Auth: dev mode 接受 `dev-token` 作为有效用户
- SSE: fetch + ReadableStream（EventSource 不支持自定义 Header）

## 关键文件

- 后端入口: `src/main.py`
- 配置: `src/core/config.py`
- 依赖注入: `src/api/deps.py`
- 前端路由: `frontend/src/App.tsx`
- 状态管理: `frontend/src/stores/adventureStore.ts`
- 启动脚本: `scripts/dev.ps1` (Windows) / `scripts/start-dev.sh` (Unix)

## 唯一阻塞

- `.env` DEEPSEEK_BASE_URL 需手动改为 `https://api.deepseek.com`（去掉 `/v1`）
- 启动脚本已覆盖此变量，直接用脚本启动可绕过

## 待办

- [ ] 覆盖率 90% → 92%+（constraint_assembler 94%）
- [ ] 生产环境部署密钥配置（VAPID / JWT / DB 密码 → GH Secrets + 环境变量）

## 行为宪法（本次会话固化）

以下规则已写入配置文件，下次会话自动加载：
- `.claude/rules/behavior.md` — 4 条红线
- `.claude/rules/autonomous.md` — 禁止词汇 + 替代表达
- SessionStart hook 会打印行为宪法摘要
- CLAUDE.md 顶部有醒目引用
