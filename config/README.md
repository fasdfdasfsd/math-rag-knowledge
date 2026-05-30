# Claude Code 四层配置 — 简明操作手册

## 体系总览

```
┌─────────────────────────────────────────────────────────┐
│                    Claude Code 开发环境                    │
│                                                         │
│  config/（配置层）           knowledge/ + .claude/rules/  │
│  ┌───────────────────┐     ┌──────────────────────┐     │
│  │ L0 组织强制        │     │ knowledge/（规范文档）   │     │
│  │ L1 用户全局        │──引用→│ .claude/rules/（路径规则）│     │
│  │ L2 项目共享        │──引用→│ 避坑汇总/闭环协议/审查   │     │
│  │ L3 项目本地        │     └──────────────────────┘     │
│  └───────────────────┘                                   │
│          │                                               │
│          │ 部署到                                        │
│          ▼                                               │
│  ~/.claude/ + 项目根/                                     │
└─────────────────────────────────────────────────────────┘
```

## 四层配置

```
L0  组织强制         ← 企业 IT 管控，个人项目跳过
══════════════════════════════════════════
L1  用户全局         ~/.claude/
    ├── CLAUDE.md    ← 全局规则、知识库索引
    ├── settings.json← API 端点 / 模型 / 超时
    └── knowledge/   ← 通用软工规范（05~10 类）
══════════════════════════════════════════
L2  项目共享         <项目根>/
    ├── CLAUDE.md    ← 项目指令、子代理策略、记忆管理
    ├── .claudeignore← Token 优化排除规则
    ├── knowledge/   ← 规范文件 + 项目管理文档
    ├── .claude/
    │   ├── settings.json     ← 9 Hooks + 24 权限规则
    │   ├── rules/            ← 路径作用域规则（5 个）
    │   ├── primer.md         ← 架构决策 (ADR)
    │   ├── activeContext.md  ← 任务进度
    │   └── MEMORY.md         ← 会话记忆
══════════════════════════════════════════
L3  项目本地         git-ignored
    ├── .claude/settings.local.json ← 个人 API key + effort=high
    └── CLAUDE.local.md             ← 个人偏好
```

## 知识库四层架构

```
L0  组织强制知识        企业合规红线（个人项目跳过）
L1  用户全局知识        ~/.claude/knowledge/（通用软工规范）
L2  项目共享知识        knowledge/（规范）+ .claude/rules/（路径规则）
L3  个人知识            CLAUDE.local.md（个人约定）
```

| 维度 | knowledge/ | .claude/rules/ |
|------|------------|----------------|
| 性质 | 参考文档 | 执行约束 |
| 加载 | 按需 Read | 路径匹配自动注入 |
| 文件数 | 75 规范 + 7 管理 | 5 个路径规则 |

## 文件清单

| 文件 | 源（config/ 模板） | 部署位置 | Git |
|------|-------------------|----------|-----|
| L1 全局指令 | `L1-用户全局/CLAUDE.md` | `~/.claude/CLAUDE.md` | N/A |
| L1 全局配置 | `L1-用户全局/settings.json` | `~/.claude/settings.json` | N/A |
| L1 知识库 | `../knowledge/` | `~/.claude/knowledge/` | N/A |
| L2 项目指令 | `L2-项目共享/CLAUDE.md` | `./CLAUDE.md` | ✅ |
| L2 Hook+权限 | `L2-项目共享/settings.json` | `./.claude/settings.json` | ✅ |
| L2 路径规则 | `.claude/rules/*.md` | `./.claude/rules/` | ✅ |
| L2 架构决策 | `L2-项目共享/primer.md` | `./.claude/primer.md` | ✅ |
| L2 任务状态 | `L2-项目共享/activeContext.md` | `./.claude/activeContext.md` | ✅ |
| L2 会话记忆 | `L2-项目共享/MEMORY.md` | `./.claude/MEMORY.md` | ✅ |
| L2 全局记忆 | `L2-项目共享/global-memory.md` | `~/.claude/projects/.../memory/` | 本地 |
| L3 本地覆盖 | `L3-项目本地/settings.local.json` | `./.claude/settings.local.json` | ❌ |
| L3 个人指令 | `L3-项目本地/CLAUDE.local.md` | `./CLAUDE.local.md` | ❌ |

## 快速部署

```bash
# ============ L1：用户全局 ============
cp config/L1-用户全局/CLAUDE.md ~/.claude/CLAUDE.md
cp config/L1-用户全局/settings.json ~/.claude/settings.json
cp -r knowledge/ ~/.claude/knowledge/

# ============ L2：项目共享 ============
cp config/L2-项目共享/CLAUDE.md ./CLAUDE.md
mkdir -p .claude .claude/rules
cp config/L2-项目共享/settings.json .claude/settings.json
cp config/L2-项目共享/primer.md .claude/primer.md
cp config/L2-项目共享/activeContext.md .claude/activeContext.md
cp config/L2-项目共享/MEMORY.md .claude/MEMORY.md
# .claude/rules/ 和 .claudeignore 已直接在项目中，无需额外复制

# ============ L3：项目本地 ============
cp config/L3-项目本地/settings.local.json .claude/settings.local.json
cp config/L3-项目本地/CLAUDE.local.md ./CLAUDE.local.md
```

## 9 Hooks 速查

| Hook | 触发时机 | matcher 模式 | 作用 |
|------|----------|-------------|------|
| PreToolUse ×3 | Bash 调用前 | `rm -rf` / `git push.*main` / `git push.*master` / `git commit` | 拦截危险命令（matcher 含空格=正则匹配命令内容） |
| PostToolUse ×1 | 编辑 .py 后 | `Edit` / `Write` | ruff format（待启用，当前 no-op） |
| Notification ×2 | 权限请求 / 空闲 | `permission_prompt` / `idle_prompt` | 桌面提醒 |
| PreCompact ×1 | 上下文压缩前 | — | 保存关键信息 |
| Stop ×1 | 会话结束 | — | 写入时间戳 + git diff + 记忆提醒 |
| SessionStart ×1 | 会话启动 | — | 记忆健康 + 项目状态 + 避坑审计 |

> ⚠️ Hook 配置关键规则：`matcher` 纯字母=工具名匹配，含空格/特殊字符=正则匹配命令内容。不要同时用 `matcher: "Bash"` + `if` 条件。

## 验证清单

- [ ] SessionStart 输出记忆文件 ✅ + 健康摘要
- [ ] `rm -rf /tmp/test` 被阻止
- [ ] `git push origin main` 被阻止
- [ ] `.env` 读取被拒绝
- [ ] L1 引用：`@~/.claude/knowledge/06-安全规范/03-密钥与认证管理.md`
- [ ] L2 规范引用：`knowledge/01-Token成本优化/01-Prompt缓存策略.md`
- [ ] L2 路径规则：编辑 `src/api/` 下的文件时 api.md 规则自动生效

## 目录结构总览

```
项目根/
├── config/                     ← 配置源
│   ├── README.md               ← 本手册
│   ├── L0~L3/                  ← 四层模板
│
├── CLAUDE.md                   ← L2 项目指令
├── CLAUDE.local.md             ← L3 个人指令
├── .claudeignore               ← Token 优化
├── .claude/
│   ├── settings.json           ← L2 Hooks + 权限
│   ├── settings.local.json     ← L3 本地覆盖
│   ├── rules/                  ← L2 路径作用域规则
│   ├── primer.md / activeContext.md / MEMORY.md
│
├── knowledge/                  ← 规范 + 管理文档
│   ├── README.md
│   ├── 01~10/ (75 规范)
│   └── 项目管理/ (8 文档)
│
├── .gitignore / .env.example / pyproject.toml / .mcp.json
```
