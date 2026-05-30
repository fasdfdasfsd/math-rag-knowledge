---
name: session-2026-05-30-v4.2-planning
description: v4.1 安装审计 → 安全加固 → 双维度能力分析 → v4.2 必选扩展清单
metadata:
  type: project
  session_date: 2026-05-30
---

# 会话记忆 — 2026-05-30（v4.1 审计 + v4.2 规划）

## 完成事项

### 1. v4.1 安装审计（6 问题修复）
- 方案文档 Hook 数量 7→9（补充 Notification ×2）
- config/README.md + config/L2/README.md 数字同步（Hook 8→9, knowledge 66→82）
- **创建 .gitignore**（关键：L3 文件无保护）
- **创建 config/L2/.claudeignore 模板** + 部署脚本自动修复
- PostToolUse matcher+if 修复（`Edit|Write`+`if` → 拆分为 Edit / Write 两个独立条目）
- 避坑 #12 归档

### 2. 安全加固
- **L3 Bash(*) 发现并移除**（用户指正 — 完全绕过 L2 安全模型）
- L3 恢复为仅 WebSearch + WebFetch 域限制
- Git 初始化：4 次提交，118 文件
- .gitignore 修复：`/CLAUDE.local.md` 仅匹配根目录，避免误伤 config/L3 模板

### 3. 自动化验证体系
- `scripts/audit_v4.1.py` — 610 检查项静态审计（100% 通过）
- `scripts/func_test_v4.1.py` — 50 项功能测试（100% 通过）
- 避坑 #13 归档（L3 Bash(*)）
- 避坑汇总 10→12 条

### 4. v4.2 第三方扩展规划
- 双维度分析：生命周期轴（9 阶段）+ 基础能力域（9 域）= 18 能力域
- v4.1 + Claude Code 内置覆盖 11 域，真实缺口 7 个
- 排除 7 个"看似有用不填补缺口"的工具
- 输出 `plugins/必选扩展清单-v4.2.md`（365 行，待用户确认后安装）

### 5. v4.2 必选 7 项

| # | 必选项 | 填补缺口 | 许可 | 费用 |
|---|--------|------|:--:|:--:|
| 1 | E2B | 测试沙箱 + 代码安全 | Apache 2.0 | 免费 |
| 2 | GitHub MCP | CI/CD 协作中枢 | MIT | 免费 |
| 3 | Context7 | 实时库文档 | MIT | 免费 |
| 4 | Snyk Scanner | 自动化安全扫描 | Apache 2.0 | 免费 |
| 5 | PostgreSQL MCP | 数据库操作能力 | MIT | 免费 |
| 6 | Brave Search MCP | Web 技术搜索 | MPL 2.0 | 免费 |
| 7 | Playwright MCP | 浏览器自动化 | Apache 2.0 | 免费 |

## 重要决策
- 选型方法论：先定义能力缺口，再选工具填补（而非先选工具再找理由）
- L3 权限原则：不放任何 Bash 权限，所有 Bash 控制在 L2 统一管理
- 三不选原则：v4.1 已覆盖不选、Claude Code 内置不选、当前阶段不需要不选
- 四层架构扩展：新增"扫描层"（Snyk，不入 L1/L2/L3，独立守护）

## 避坑新增
12. PostToolUse `Edit|Write` + `if` 不可靠（同 #9 家族 — `|` 属于工具名字符集，`if` 可能被忽略）
13. L3 `Bash(*)` 覆盖 L2 全部安全模型（部署时临时加入，事后忘记移除）

## 下次会话
1. 用户确认 `plugins/必选扩展清单-v4.2.md`
2. 按三阶段安装 7 个 MCP
3. 安装后验证（11 项清单）
4. 更新 v4.1 审计脚本适配 v4.2
