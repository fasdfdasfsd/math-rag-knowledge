# Claude Code 四层配置 — 部署手册

> 版本：v4.1 | 日期：2026-05-30

## 部署概览

```
部署源                     部署目标
───────────────────────────────────────────
config/L1-用户全局/     →   ~/.claude/
config/L2-项目共享/     →   <项目根>/ + <项目根>/.claude/ + .claude/rules/
config/L3-项目本地/     →   <项目根>/.claude/ + <项目根>/
knowledge/              →   <项目根>/knowledge/（已存在）+ ~/.claude/knowledge/
```

## 前置条件

| 条件 | 检查方式 |
|------|----------|
| Git 已安装 | `git --version` |
| Claude Code 已安装 | `claude --version` |
| 项目已克隆 | `ls CLAUDE.md` |

## 一键部署

### Ubuntu
```bash
chmod +x deploy/install.sh
./deploy/install.sh
```

### Windows 11
```powershell
.\deploy\install.ps1
```

## 部署步骤详情

### Step 1：L1 用户全局

| 文件 | 源 | 目标 |
|------|-----|------|
| 全局指令 | `config/L1-用户全局/CLAUDE.md` | `~/.claude/CLAUDE.md` |
| 全局配置 | `config/L1-用户全局/settings.json` | `~/.claude/settings.json` |
| 知识库 | `knowledge/` | `~/.claude/knowledge/` |

### Step 2：L2 项目共享

| 文件 | 源 | 目标 |
|------|-----|------|
| 项目指令 | `config/L2-项目共享/CLAUDE.md` | `./CLAUDE.md` |
| Hook+权限 | `config/L2-项目共享/settings.json` | `./.claude/settings.json` |
| Token优化 | 项目根已有 | `./.claudeignore` |
| 路径规则 | `.claude/rules/`（5 文件） | `./.claude/rules/` |
| 架构决策 | `config/L2-项目共享/primer.md` | `./.claude/primer.md` |
| 任务状态 | `config/L2-项目共享/activeContext.md` | `./.claude/activeContext.md` |
| 会话记忆 | `config/L2-项目共享/MEMORY.md` | `./.claude/MEMORY.md` |

### Step 3：L3 项目本地

| 文件 | 源 | 目标 |
|------|-----|------|
| 本地覆盖 | `config/L3-项目本地/settings.local.json` | `./.claude/settings.local.json` |
| 个人指令 | `config/L3-项目本地/CLAUDE.local.md` | `./CLAUDE.local.md` |

### Step 4：全局记忆目录

```bash
mkdir -p ~/.claude/projects/D--panzt-projects-claude-code-python-rag/memory/
```

## 部署后验证

1. 重启 Claude Code（在项目目录打开）
2. 应看到 SessionStart 输出：
   ```
   ═══ 记忆文件状态 ═══
   ✅ .claude/MEMORY.md
   ✅ .claude/primer.md
   ✅ .claude/activeContext.md
   ✅ CLAUDE.md
   ═══ 项目健康检查 ═══
   ...
   ══════════════════
   ```
3. 验证 Hook：尝试 `rm -rf /tmp/test` 应被阻止
4. 验证知识库：`@knowledge/README.md` 应可引用
5. 编辑 `src/api/` 下的 .py 文件，验证 api.md 规则自动注入

## 故障排查

| 症状 | 可能原因 | 解决 |
|------|----------|------|
| SessionStart 无输出 | settings.json 未部署到 .claude/ | 检查 `.claude/settings.json` 存在 |
| Hook 不生效 | 权限未覆盖 L2 规则 | 检查 settings.local.json 有无冲突 |
| **所有 Bash 被误拦截** | `matcher: "Bash"` + `if` 条件组合失效 | 改用 `matcher: "git push.*main"`（含空格=正则），去掉 `if` 字段 |
| 知识库 @ 引用失败 | knowledge/ 目录缺失 | 确认 `knowledge/` 目录存在 |
| 路径规则不注入 | rules/ 未部署 | 检查 `.claude/rules/` 目录 |
