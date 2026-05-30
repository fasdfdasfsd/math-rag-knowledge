---
title: 开发流程与 Git 规范
id: SE-04
priority: must
category: 软件工程生命周期
tags: [git-flow, trunk-based, conventional-commits, branch-naming, pr-review, pre-commit]
description: 开发流程中 Git 分支策略、提交信息规范、PR/MR 流程及 Code Review 要求
---

# 开发流程与 Git 规范

## 概述

统一 Git 规范是团队协作的基础，直接影响代码质量和交付效率。本规范涵盖 Git Flow 与 Trunk-Based Development 两种分支策略的选择、Conventional Commits 提交规范、分支命名规则、PR/MR 流程、Code Review 要求及 pre-commit hooks 配置。

---

## 核心规则

### MUST（必须遵守）

1. **MUST - Commit Message 遵循 Conventional Commits 格式**
   ```txt
   <type>(<scope>): <description>
   <BLANK LINE>
   <body> (optional)
   <BLANK LINE>
   <footer> (optional)
   ```

2. **MUST - 分支命名遵循统一规范**
   - `feature/TICKET-123-short-description`（功能）
   - `fix/TICKET-123-short-description`（修复）
   - `chore/TICKET-123-short-description`（工程）
   - `docs/TICKET-123-short-description`（文档）

3. **MUST - 禁止直接向 main/master 分支推送代码**
   - 所有变更必须通过 PR/MR 合并

4. **MUST - PR 标题与首个 Commit Message 一致**
   - 便于 squash merge 后保持历史清晰

5. **MUST - 合并前通过所有 CI 检查**
   - Lint、测试、构建、安全扫描必须全部通过

### SHOULD（应该遵守）

1. **SHOULD - 每个 Commit 保持原子性**
   - 一个 Commit 只做一件事，便于回滚和审查
   - 避免"fix typo"类 Commit 出现在最终历史中

2. **SHOULD - 分支生命周期管理**
   - 功能分支不超过 3 天，超过应拆分或定期合并 main

3. **SHOULD - 配置 pre-commit hooks 做本地检查**
   - 至少包含：代码格式化、Lint、密钥检测

4. **SHOULD - PR 描述须包含背景和测试说明**
   - What（改了啥）→ Why（为什么改）→ How（怎么验证）

### MAY（可以遵守）

1. **MAY - 使用 git-rebase 保持历史线性**
2. **MAY - 配置 Commit lint 自动化校验**
3. **MAY - 使用 Gitmoji 增强提交信息表达**

---

## 流程与检查清单

### 分支策略对比

| 特性 | Git Flow | Trunk-Based Development |
|------|----------|------------------------|
| 适用团队 | 大型团队、需要长期维护版本 | 中小型团队、持续交付 |
| 主要分支 | main, develop, release, hotfix | main (trunk) |
| 分支生命周期 | 较长（数天~数周） | 极短（数小时~1天） |
| 合并频率 | 低（feature → develop） | 高（每日多次合并 trunk） |
| 复杂度 | 高 | 低 |
| CI/CD 适配 | 中 | 强 |

**选择建议**：
- 发版频率低于每周 → Git Flow
- 发版频率高于每天 → Trunk-Based Development
- SaaS 产品 → Trunk-Based Development
- 嵌入式/硬件绑定的软件 → Git Flow

### Conventional Commits 类型速查

| Type | 含义 | 是否触发版本号 |
|------|------|--------------|
| feat | 新功能 | MINOR（次要版本） |
| fix | Bug 修复 | PATCH（补丁版本） |
| BREAKING CHANGE | 不兼容变更 | MAJOR（主版本） |
| docs | 文档变更 | 否 |
| style | 代码样式（格式化等） | 否 |
| refactor | 重构 | 否 |
| perf | 性能优化 | 否 |
| test | 测试相关 | 否 |
| chore | 工程配置 | 否 |
| ci | CI/CD 配置 | 否 |

### PR/MR 模板

```markdown
## 描述
[简要描述本次 PR 的内容和背景]

## 关联 Issue
Closes #TICKET-123

## 变更类型
- [ ] feat: 新功能
- [ ] fix: Bug 修复
- [ ] refactor: 重构
- [ ] docs: 文档
- [ ] test: 测试
- [ ] chore: 工程

## 测试说明
- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] 手动测试完成

## 影响范围
- 影响的服务/模块：[列举]

## 截图（如有）
[UI 变更时附 before/after 截图]

## 检查清单
- [ ] 代码遵循项目编码规范
- [ ] 已添加/更新测试
- [ ] 文档已更新
- [ ] Commit Message 符合规范
- [ ] 无敏感信息泄露（密钥、IP、Token）
```

### pre-commit hooks 配置（.pre-commit-config.yaml）

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: detect-private-key

  - repo: https://github.com/commitizen-tools/commitizen
    rev: v3.12.0
    hooks:
      - id: commitizen

  - repo: local
    hooks:
      - id: lint
        name: Lint Check
        entry: npm run lint
        language: node
        types: [javascript]
```

### 开发流程检查清单

| 阶段 | 检查项 |
|------|--------|
| 开始开发 | 从最新 main 拉取新分支？分支命名符合规范？ |
| 开发中 | Commit 是否原子化？Message 格式正确？pre-commit 是否通过？ |
| 提交 PR | PR 模板填写完整？关联 Issue？CI 是否通过？ |
| Code Review | 至少 1 人 Review 通过？Reviewer 是否相关领域专家？ |
| 合并 | 是否 rebase 到最新 main？是否 squash merge？ |
| 合并后 | 分支是否删除？CI 是否通过？ |

---

## 参考来源

- Conventional Commits - https://www.conventionalcommits.org
- Git Flow - Vincent Driessen
- Trunk-Based Development - Paul Hammant
- Semantic Versioning - https://semver.org
- pre-commit - https://pre-commit.com
- Google Engineering Practices - https://google.github.io/eng-practices
