# L1 — 用户全局层

> 部署位置：`~/.claude/`

## 包含文件

| 文件 | 部署位置 | 说明 |
|------|----------|------|
| `CLAUDE.md` | `~/.claude/CLAUDE.md` | 全局规则 + 知识库索引（引用 05~10 类） |
| `settings.json` | `~/.claude/settings.json` | API 端点 / 模型选择 / 超时 |
| `../knowledge/05~10/` | `~/.claude/knowledge/` | 通用软工规范（44 个文件） |

## 部署步骤

### 1. 部署 CLAUDE.md
```bash
cp config/L1-用户全局/CLAUDE.md ~/.claude/CLAUDE.md
```

### 2. 部署 settings.json
```bash
# 先编辑 config/L1-用户全局/settings.json，填入你的 API 密钥
# ANTHROPIC_AUTH_TOKEN 字段
cp config/L1-用户全局/settings.json ~/.claude/settings.json
```

### 3. 部署知识库（通用规范 05~10 类）
```bash
# 从项目 knowledge/ 复制全部到全局目录
cp -r knowledge/ ~/.claude/knowledge/
```

> 全局知识库存放跨项目通用的软工规范（编程语言、安全、数据库、生命周期、国标、工程基础）。项目级规范（01~04）通过项目的 knowledge/ 引用。

## 知识库引用验证

部署后，在任意项目的 Claude Code 会话中测试：

```
@~/.claude/knowledge/06-安全规范/03-密钥与认证管理.md
@~/.claude/knowledge/05-编程语言规范/Python-PEP8与编码规范.md
@~/.claude/knowledge/07-数据库规范/PostgreSQL规范.md
```

> ⚠️ L1 CLAUDE.md 中的目录编号（05-10）必须与 `~/.claude/knowledge/` 下的实际目录名严格一致。

## 验证
重启 Claude Code，在任意项目目录下应自动加载全局规则。
