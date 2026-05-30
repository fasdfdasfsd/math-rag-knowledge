---
name: session-2026-05-30-v4.1-audit
description: v4.1 安装审计，发现并修复 6 个问题
metadata:
  type: project
  session_date: 2026-05-30
---

# 会话记忆 — 2026-05-30（v4.1 安装审计）

## 审计方法
模拟从零部署流程，逐项检查方案文档、config/ 模板、deploy/ 脚本、实际部署文件之间的一致性。

## 发现的 6 个问题（全部已修复）

### 1. 方案 §四 Hook 数量不一致（设计缺失）
- **问题**：方案写 7 个 Hook，实际 settings.json 有 9 个
- **根因**：Notification ×2（permission_prompt + idle_prompt）未在设计文档中说明
- **修复**：方案 §四 完整列出 9 个 Hook 的设计意图

### 2-3. 文档中 Hook/知识库数字过时
- config/README.md、config/L2/README.md、方案 §二/§十：Hook 数量写 7 或 8，统一改为 9
- knowledge 文件数 66→82

### 4. 缺少 .gitignore（关键）
- **风险**：CLAUDE.local.md、.claude/settings.local.json、.env、*.pem 可能被误提交
- **修复**：创建完整 .gitignore，覆盖 L3 文件 + 密钥 + Python 标准忽略

### 5. .claudeignore 无模板备份
- **问题**：部署脚本只警告不修复
- **修复**：创建 config/L2/.claudeignore 模板，部署脚本改为自动复制

### 6. PostToolUse matcher+if 不可靠（避坑 #12）
- **问题**：`matcher: "Edit|Write"` + `if` — `|` 属于工具名字符集，`if` 可能被忽略
- **修复**：拆分为两个独立条目（`matcher: "Edit"` / `matcher: "Write"`），去掉 `if`

## 同步更新的文件
| 文件 | 变更 |
|------|------|
| knowledge/方案设计.md | Hook 7→9 + 避坑 #12 + 实施索引补充 |
| config/README.md | Hook 8→9，更新速查表 |
| config/L2/README.md | Hook 8→9，knowledge 66→82 |
| config/L2/settings.json | PostToolUse 拆分 |
| .claude/settings.json | PostToolUse 拆分 |
| .gitignore | 新建 |
| config/L2/.claudeignore | 新建模板 |
| deploy/install.sh | .claudeignore 自动修复 |
| deploy/install.ps1 | .claudeignore 自动修复 |
| .claude/activeContext.md | 更新任务状态 |
