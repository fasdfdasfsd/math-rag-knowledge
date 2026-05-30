# 全局记忆目录模板

> 部署位置：`~/.claude/projects/D--panzt-projects-claude-code-python-rag/memory/`

## 目录说明

Claude Code 的自动记忆系统在此目录下读写记忆文件。每个记忆一个 `.md` 文件，`MEMORY.md` 为索引。

## 部署步骤

```bash
mkdir -p ~/.claude/projects/D--panzt-projects-claude-code-python-rag/memory/
```

## MEMORY.md（索引文件）

```markdown
# 项目记忆索引

> python-rag 项目记忆目录
> 每个记忆一个 .md 文件，本文件为索引

## 记忆列表

（暂无记忆条目，重要决策后自动添加）
```

## 单个记忆文件模板

文件名：`<kebab-case-slug>.md`

```markdown
---
name: <kebab-case-slug>
description: <一句话摘要，用于检索匹配>
metadata:
  type: user | feedback | project | reference
---

<记忆正文>

**Why:** <为什么做这个决策>
**How to apply:** <如何在后续工作中应用>

关联：[[related-memory-name]]
```

## 记忆类型

| type | 用途 | 示例 |
|------|------|------|
| `user` | 用户偏好、背景 | 用户是全栈开发者，偏好中文 |
| `feedback` | 用户反馈、纠正 | 用户要求用 uv 而非 pip |
| `project` | 项目决策、架构 | 选择 pgvector 作为向量数据库 |
| `reference` | 外部资源引用 | API 文档链接、issue 链接 |

## 何时写入

由 CLAUDE.md 的记忆管理规则驱动：
- 即时写入触发条件满足时（决策/bug修复/避坑/阶段完成/PreCompact）
- 会话结束时
