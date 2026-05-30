---
category: 项目管理
priority: must
updated: 2026-05-30
version: 4.1
status: locked
milestone: v4.1-20260530
---

# Claude Code 软件工程初始化方案设计

> 性质：设计文档（设计意图 + 架构决策 + 实施索引）
> 配置源码：`config/` | 部署手册：`config/README.md` | 知识库：`knowledge/`

---

## 一、设计目标

### 要解决的问题

Claude Code 开箱即用，但缺少系统化的软件工程约束：

| 痛点 | 后果 |
|------|------|
| 无统一编码规范 | 每次对话都要重复交代规则，浪费 Token |
| 无安全检查 | 可能误执行 `rm -rf`、`dropdb`、`git push --force` |
| 会话记忆丢失 | 上下文压缩或退出后，重要决策消失，下次从头开始 |
| 无权限控制 | Claude 可能读取 `.env` 中的密钥或执行危险命令 |
| 配置散落 | 换了项目或机器，环境要重新搭建 |

### 设计原则

1. **分层隔离**：个人偏好 / 项目规则 / 组织强制 互不干扰
2. **约定优于配置**：提供完整默认值，个性化只需覆盖 L3
3. **防御纵深**：CLAUDE.md 指令（第一道）+ settings.json Hook（第二道）
4. **即时持久化**：不等会话结束，关键节点立即写记忆
5. **设计/实现分离**：方案管「为什么」，config/ 管「怎么做」

---

## 二、系统架构

### 四层配置体系

```
L0  组织强制（系统目录）          ← 企业 IT 管控，个人项目跳过
══════════════════════════════════════════════════════════
L1  用户全局  ~/.claude/          ← 跨项目通用
    ├── CLAUDE.md                ← 安全红线、知识库索引、编码原则
    ├── settings.json            ← API 端点、模型、超时
    └── knowledge/               ← 通用软工规范（05~10 类，44 文件）
──────────────────────────────────────────────────────────
L2  项目共享  项目根/              ← Git 版本控制
    ├── CLAUDE.md                ← 项目身份、架构约定、子代理策略、记忆管理
    └── .claude/
        ├── settings.json        ← 9 Hooks + 24 权限规则
        ├── primer.md            ← 架构决策记录 (ADR)
        ├── activeContext.md     ← 当前任务状态
        ├── MEMORY.md            ← 会话记忆
        └── global-memory.md     ← 全局记忆模板（部署到 ~/.claude/projects/）
──────────────────────────────────────────────────────────
L3  项目本地  git-ignored         ← 个人覆盖
    ├── .claude/settings.local.json  ← 个人 API key
    └── CLAUDE.local.md              ← 个人偏好
```

### 优先级规则

```
L3（本地覆盖）> L2（项目共享）> L1（用户全局）> L0（组织强制）
```

### 配置-知识库协作模型

```
CLAUDE.md  ──引用──→  knowledge/     （告诉 Claude「查什么规范」）
settings.json ──执行──→ Hooks         （阻止 Claude 违反规范）
knowledge/ ──定义──→  规范内容         （规范本身是什么）
避坑汇总    ──反馈──→  knowledge/     （经验持续积累）
```

---

## 三、各层设计意图

### L1 — 用户全局

**为什么需要**：同一用户的所有项目共享通用规则，避免每个项目重复配置。

| 文件 | 意图 | 关键决策 |
|------|------|----------|
| `CLAUDE.md` | 安全红线（所有项目必须遵守）、知识库索引 | L1 知识库只放通用规范，项目专属规范在 L2 |
| `settings.json` | API 端点统一走 DeepSeek，模型分级 flash/pro，超时 10 分钟 | `SUBAGENT_MODEL=flash` 降低 Token 消耗 |
| `knowledge/` | 05~10 类通用软工规范 | `@~/.claude/knowledge/` 跨项目绝对路径引用 |

### L2 — 项目共享

**为什么需要**：项目专属规则需团队共享、Git 版本控制、Hook 拦截危险操作。

| 文件 | 意图 | 关键决策 |
|------|------|----------|
| `CLAUDE.md` | 项目身份 + 编码前必读 knowledge/ + 子代理策略 + 硬性记忆管理 | 记忆管理升级为「MUST」，5 个即时写入触发条件 |
| `settings.json` | 9 Hooks + 24 权限规则 | `includes` 子串匹配代替正则；权限按最小粒度细化 |
| `primer.md` | 架构决策记录（5 个 ADR） | 架构变更时同步更新 |
| `activeContext.md` | 任务进度 | 每次会话结束更新，下次启动恢复 |
| `MEMORY.md` | 会话记忆 | 即时写入 + 会话结束重写 |
| `global-memory.md` | 全局记忆模板 | 部署到 `~/.claude/projects/.../memory/` |

### L3 — 项目本地

**为什么需要**：个人密钥不入库，允许覆盖项目默认配置。

| 文件 | 意图 |
|------|------|
| `settings.local.json` | 个人 API key，覆盖 L1/L2 同名配置 |
| `CLAUDE.local.md` | 个人偏好（OS、工作目录、编码习惯） |

**安全**：两个文件均在 `.gitignore` 中排除，禁止提交。

---

## 四、Hook 体系设计

### 设计原则

- **默认阻止，显式允许**：危险操作一律拦截
- **最小权限**：Bash Allow 只开必要的命令，且细化到具体子命令
- **纵深防御**：CLAUDE.md 指令（第一道）+ settings.json Hook（第二道）
- **质量左移**：提交前强制检查，而非事后补救

### 9 个 Hook 的设计意图

| # | Hook | 触发时机 | 设计意图 |
|---|------|----------|----------|
| 1 | PreToolUse | Bash 调用前 | 拦截 `rm -rf` — 防止不可逆删除 |
| 2 | PreToolUse | Bash 调用前 | 拦截 `git push *main*` — 主分支必须通过 PR |
| 3 | PreToolUse | Bash 调用前 | `git commit` 前提醒质量门禁 — ruff + pytest + mypy |
| 4 | PostToolUse | 编辑 .py 后 | ruff format — 保证代码风格一致（待启用） |
| 5 | Notification | 权限请求弹窗 | `permission_prompt` — 桌面通知提醒用户确认许可 |
| 6 | Notification | 空闲等待输入 | `idle_prompt` — 桌面通知提醒用户 Claude 在等待 |
| 7 | PreCompact | 上下文压缩前 | 提醒保存关键信息 — 防止压缩导致记忆丢失 |
| 8 | Stop | 会话结束 | 写入退出时间戳（检测异常退出）+ 提醒更新记忆 |
| 9 | SessionStart | 会话启动 | 记忆健康 + 项目健康摘要 + 避坑审计

### Hook #3：自动化质量门禁

**设计意图**：CLAUDE.md 声明「Ruff 零警告」「覆盖率 ≥80%」，但没有机制强制执行。`git commit` 前提醒执行检查。

```
git commit → Hook 拦截 → 提醒执行质量门禁 →
  ├── ruff check .          → 零警告
  ├── mypy --strict src/    → 零错误
  └── python -m pytest --cov=src → ≥80%
```

> 注意：Hook 当前为「提醒」而非「阻止」。待 CI 流水线建立后，阻止可以移到远程端。

### Hook #7：项目健康摘要

**设计意图**：每次会话启动时，一眼判断项目整体状态，而非仅看记忆文件。

```
═══ 记忆文件状态 ═══
✅ .claude/MEMORY.md
✅ .claude/primer.md
✅ .claude/activeContext.md
✅ CLAUDE.md

═══ 项目健康检查 ═══
📅 上次退出: 2026-05-30T14:30:00
🧪 测试: ⚠️ 上次有失败用例
📝 避坑: MEMORY.md 中有未归类经验
══════════════════
```

### Hook 配置关键规则（避坑 #11）

**`matcher` 字段的双重语义**：

| matcher 值 | 行为 | 示例 |
|-----------|------|------|
| 纯字母/数字/`_`/`\|` | 精确匹配**工具名** | `"Bash"` → 匹配所有 Bash 调用 |
| 含空格/特殊字符 | **正则匹配命令内容** | `"git push.*main"` → 只匹配含 `git push` 和 `main` 的命令 |

**错误写法**：
```json
{ "matcher": "Bash", "if": "tool_input.command includes 'git push' && ..." }
// ❌ matcher="Bash" 匹配所有 Bash，if 条件被忽略，导致全部 Bash 被拦截
```

**正确写法**：
```json
{ "matcher": "git push.*main" }
// ✅ matcher 含空格 → 自动转为正则，只匹配 "git push ... main" 的命令
{ "matcher": "rm -rf" }
// ✅ 含空格 → 只匹配包含 "rm -rf" 的命令
```

**结论**：不要同时使用 `matcher: "Bash"` + `if` 条件。直接将匹配模式写入 `matcher` 字段（含空格触发正则）。

---

## 五、权限模型设计

### 最小权限 + 最小粒度

```
v4.0：Bash(python *) — 允许执行任何 Python 代码
v4.1：Bash(python -m pytest *) + Bash(python -m ruff *) + Bash(python -m mypy *) — 只允许测试和检查

v4.0：Bash(curl *) — 允许任意 HTTP 请求
v4.1：Bash(curl http://localhost:*) + Bash(curl https://api.deepseek.com:*) — 只允许本地和 API 端点
```

### Allow 分类逻辑

| 类别 | 命令 | 理由 |
|------|------|------|
| 版本控制 | `git *` | 开发必备，PreToolUse 拦截危险操作 |
| 包管理 | `uv *` | 比 pip 安全，不执行远程代码 |
| 测试 | `python -m pytest *` | 仅运行测试框架 |
| 检查 | `python -m ruff *`, `python -m mypy *` | 静态分析，无副作用 |
| 部署 | `python deploy.py *` | 仅项目部署脚本 |
| 只读 | `ls/cat/find/wc *` | 纯读取 |
| 目录 | `mkdir` | 低频操作 |
| 网络 | `curl http://localhost:*`, `curl https://api.deepseek.com:*` | 限制端点和域名 |
| 工具 | `echo *` | Hook 中输出信息 |

### Deny 分类逻辑

| 类别 | 规则 | 理由 |
|------|------|------|
| 不可逆操作 | `rm -rf`, `dropdb` | 数据删除无法恢复 |
| 主分支保护 | `git push --force`, `git push *main*` | 必须通过 PR |
| 密钥保护 | `Read(**/*.env)`, `Read(**/*.pem)`, `Read(**/*.key)`, `Read(**/secrets/**)` | 防止 Claude 读取敏感信息 |

---

## 六、知识库体系设计

### 四层架构

知识库与配置体系共享同一四层模型：

```
L0  组织强制知识           企业合规红线（个人项目跳过）
══════════════════════════════════════════════════════════
L1  用户全局知识            ~/.claude/knowledge/
    通用软工规范            编程语言/安全/数据库/生命周期/国标/工程基础
    加载方式：@~/.claude/knowledge/ 绝对路径引用
    部署：cp -r knowledge/ ~/.claude/knowledge/（一次性）
──────────────────────────────────────────────────────────
L2  项目共享知识            knowledge/（规范文件）+ .claude/rules/（路径规则）
    ├── knowledge/01~04/    项目专属规范（RAG/Token/Python生态）
    ├── knowledge/05~10/    通用规范副本（方便项目内引用）
    ├── knowledge/项目管理/  设计文档、模板规范、映射表、闭环协议、审查协议
    └── .claude/rules/      路径作用域规则（YAML paths → 按需注入）
──────────────────────────────────────────────────────────
L3  个人知识                git-ignored
    CLAUDE.local.md         个人偏好/约定/本地环境信息
```

### 两层内容体系

```
knowledge/（规范文件 — 详尽的指南和参考）        .claude/rules/（路径规则 — 简洁的执行约束）
├── 01~04/ 项目专属规范                          ├── python.md     → src/**/*.py
├── 05~10/ 通用规范                              ├── api.md        → src/api/**/*.py
├── 知识文件模板规范.md                           ├── database.md   → src/repositories/**/*.py
├── 规则强制执行映射表.md                          ├── security.md   → 全局
├── 知识反馈闭环协议.md                           └── testing.md    → tests/**/*.py
├── 知识审查协议.md
└── 避坑汇总.md
```

**knowledge/ vs .claude/rules/ 分工**：

| 维度 | knowledge/ | .claude/rules/ |
|------|------------|----------------|
| 性质 | 参考文档（详尽） | 执行约束（简洁） |
| 加载 | CLAUDE.md 索引 → 按需 Read | 路径匹配 → 自动注入 |
| Token 成本 | 需要时才加载 | 接触匹配文件时自动注入 |
| 更新 | 知识反馈闭环 | 规则变更时 |

### 引用方式

| 层级 | 语法 | 示例 |
|------|------|------|
| L1 | `@~/.claude/knowledge/` | `@~/.claude/knowledge/06-安全规范/03-密钥与认证管理.md` |
| L2 规范 | `knowledge/` 相对路径 | `knowledge/01-Token成本优化/01-Prompt缓存策略.md` |
| L2 规则 | 自动注入 | Claude 编辑 `src/api/user.py` → `api.md` 规则自动生效 |

### 知识反馈闭环

```
避坑产生 ──→ MEMORY.md（即时记录）
     │
     ▼
SessionStart 提醒 ──→ 未归类避坑: N 条
     │
     ▼
人工确认 ──→ knowledge/避坑汇总.md（归类归档）
     │
     ▼
验证通用性 ──→ knowledge/ 对应规范文件（长期沉淀）
     │
     ▼
涉及具体路径 ──→ .claude/rules/ 路径规则（自动执行）
```

**设计意图**：知识库不应该是静态的。每次会话产生的避坑经验，经过五阶段闭环（捕获→提醒→归类→固化→审查），最终流入 knowledge/ 规范和 .claude/rules/ 规则，形成持续积累。

---

## 七、记忆持久化设计

### 核心问题

Stop hook 只能运行 shell 命令，**无法强制 Claude 写入文件**。依赖会话结束时 Claude 自觉写记忆不可靠。

### 解决方案：即时写入触发

满足**任一**条件，Claude 必须立即 Write，不等到会话结束：

| # | 触发条件 | 设计理由 |
|---|----------|----------|
| 1 | 用户做出影响后续的决策 | 决策信息价值最高，丢失难恢复 |
| 2 | 发现并修复 bug/配置错误 | 避坑经验不记则下次重犯 |
| 3 | 产生新的避坑教训 | 同上 |
| 4 | 完成阶段性任务 | 进度不记则下次不知道做到哪 |
| 5 | PreCompact 触发 | 上下文压缩前最后抢救机会 |

### 三层记忆架构

| 层 | 文件 | 性质 | 更新时机 |
|----|------|------|----------|
| 静态层 | CLAUDE.md | 永久规则 | 手动编辑 |
| 动态层 | primer.md + activeContext.md | 可变状态 | 会话结束 / 架构变更 |
| 自动层 | MEMORY.md + knowledge/避坑汇总.md | 会话记录 + 经验沉淀 | 即时写入 + 定期归类 |

### 三钩防丢失

```
PreCompact ──→ 保存关键信息（压缩前最后机会）
Stop ────────→ 写入时间戳 + 最终更新记忆
SessionStart → 记忆健康 + 项目健康 + 避坑审计
```

---

## 八、子代理协作策略

### 设计意图

Claude Code 内置 Agent/Workflow 工具，支持并行和流水线两种模式。不需要引入外部编排框架（如 CrewAI），通过在 CLAUDE.md 中明确使用策略即可充分发挥。

### 模型分级

| 任务复杂度 | 模型 | 方式 |
|-----------|------|------|
| 单文件修改、简单问答 | deepseek-v4-flash | `Agent(task, {model: "haiku"})` |
| 多文件重构、架构设计 | deepseek-v4-pro | `Agent(task)` |
| 并行搜索、批量检查 | deepseek-v4-flash | `parallel([...])` |
| 多阶段流水线 | flash + pro 混合 | `pipeline(items, stage1, stage2)` |

### parallel vs pipeline 选择

```python
// ✅ parallel: 需要所有结果汇总才能继续
//    例：多维度审查后合并报告
parallel([review_security, review_perf, review_style])

// ✅ pipeline: 每个 item 独立流经多阶段
//    例：多文件逐个审查→修复→验证
pipeline(files, review, fix, verify)

// ⚠️ barrier 反模式：不要把 pipeline 中间结果收集后用 parallel 再展开
//    默认优先用 pipeline，只有真正需要跨 item 聚合时才用 parallel
```

### 约束

- 子代理默认用 flash 模型（由 L1 `CLAUDE_CODE_SUBAGENT_MODEL` 控制）
- 结构化输出指定 schema 参数，避免解析失败
- 并行文件修改用 `isolation: "worktree"` 避免冲突
- 子代理结果由主代理合成，不直接回复用户

---

## 九、避坑记录

| # | 问题 | 原因 | 解决方案 | 设计启示 |
|----|------|------|----------|----------|
| 1 | `matches` 正则误拦截 | 正则过宽 | `includes` 子串匹配 | 安全拦截用精确匹配 |
| 2 | 自动模式阻止写 settings.json | Claude Code 安全机制 | 用户手动覆盖 | L3 文件需预先创建 |
| 3 | `git push origin main` 可被变体绕过 | 精确匹配不够 | `includes 'main'` | 子串匹配防变体 |
| 4 | RAG 任务超时 | 默认 5 分钟 | `API_TIMEOUT_MS=600000` | 复杂任务需更长超时 |
| 5 | SessionStart 与 CLAUDE.md 不一致 | hook 未随方案更新 | hook 对齐 CLAUDE.md 记忆流程 | 改方案必须同步检查 hook |
| 6 | Stop hook 无法强制写记忆 | shell 无法驱动 Claude | CLAUDE.md 硬性指令 + 即时触发 | 文件操作靠指令不靠 hook |
| 7 | L1 CLAUDE.md 知识库编号错误 | 目录 05~10，文档写 01~06 | 严格对齐实际目录名 | 引用路径必须与目录一致 |
| 8 | config/ 缺少全局 memory 模板 | 设计时遗漏 | 补充 `global-memory.md` | 模板须覆盖所有部署目标 |
| 9 | `python *` 权限过宽 | 允许任意 Python 代码 | 细化为 `python -m pytest/ruff/mypy *` | 权限按最小粒度控制 |
| 10 | `curl *` 权限过宽 | 允许任意网络请求 | 限制 localhost + api.deepseek.com | 网络权限限制端点和域名 |
| 11 | `matcher: "Bash"` + `if` 条件导致所有 Bash 被误拦截 | `if` 条件在 `matcher` 为纯字母时被忽略；`matcher` 含空格/特殊字符时自动变为正则匹配 | 用 `matcher: "git push.*main"` 直接正则匹配，去掉 `if` | 官方文档明确：matcher 纯字母=工具名精确匹配，含特殊字符=正则匹配命令内容 |
| 12 | `PostToolUse` 用 `matcher: "Edit\|Write"` + `if` 组合不可靠 | `\|` 属于「工具名」字符集，`if` 可能被忽略；`Edit\|Write` 在工具名模式下含义不明确（是字面量还是 OR？） | 拆分为两个独立 Hook 条目，一个 `matcher: "Edit"`，一个 `matcher: "Write"`，去掉 `if` | PostToolUse 同样适用避坑 #11 规则：不要同时使用 matcher + if。当 ruff 安装后，文件过滤逻辑需要重新设计 |

---

## 十、实施索引

### 配置模板 → `config/`

| 部署目标 | 模板 |
|----------|------|
| `~/.claude/CLAUDE.md` | `config/L1-用户全局/CLAUDE.md` |
| `~/.claude/settings.json` | `config/L1-用户全局/settings.json` |
| `./CLAUDE.md` | `config/L2-项目共享/CLAUDE.md` |
| `./.gitignore` | 项目根（保护 L3 文件 + 密钥） |
| `./.claudeignore` | `config/L2-项目共享/.claudeignore` |
| `./.claude/settings.json` | `config/L2-项目共享/settings.json` |
| `./.claude/primer.md` | `config/L2-项目共享/primer.md` |
| `./.claude/activeContext.md` | `config/L2-项目共享/activeContext.md` |
| `./.claude/MEMORY.md` | `config/L2-项目共享/MEMORY.md` |
| `~/.claude/projects/.../memory/MEMORY.md` | `config/L2-项目共享/global-memory.md` |
| `./.claude/settings.local.json` | `config/L3-项目本地/settings.local.json` |
| `./CLAUDE.local.md` | `config/L3-项目本地/CLAUDE.local.md` |

### 知识库 → `knowledge/` + `.claude/rules/`

| 内容 | 路径 |
|------|------|
| 规范文件（82 个） | `knowledge/01~10/` |
| 知识库索引 | `knowledge/README.md` |
| 设计文档 | `knowledge/Claude Code软件工程初始化方案设计.md` |
| 模板规范 | `knowledge/知识文件模板规范.md` |
| 规则-强制映射表 | `knowledge/规则强制执行映射表.md` |
| 知识反馈闭环协议 | `knowledge/知识反馈闭环协议.md` |
| 知识审查协议 | `knowledge/知识审查协议.md` |
| 避坑汇总 | `knowledge/避坑汇总.md` |
| 路径规则（5 个） | `.claude/rules/python.md, api.md, database.md, security.md, testing.md` |

### 操作入口

- **部署新环境** → `config/README.md` §快速部署
- **修改 Hook/权限** → 编辑 `config/L2/settings.json` → `cp` 到 `.claude/`
- **修改项目规则** → 编辑 `config/L2/CLAUDE.md` → `cp` 到 `./CLAUDE.md`
- **查阅规范** → `knowledge/README.md` → 对应分类
- **理解设计** → 本文档

---

## 版本历史

| 版本 | 日期 | 里程碑 |
|------|------|--------|
| v1.0 | 2026-05-30 | 初始设计：4 层配置 + 知识库 + 三钩记忆 |
| v2.0 | 2026-05-30 | 记忆持久化加固（即时写入 + Hook 增强） |
| v3.0 | 2026-05-30 | 完整操作手册（1314 行，源码+部署+验证） |
| v4.0 | 2026-05-30 | 设计/实现分离（293 行设计 + config/ 模板） |
| v4.1 | 2026-05-30 | 🔒 锁定版本：6 补足 + 子代理策略 + 四层知识库 + L2 模块化规则（425 行） |

> 📐 本文档解决「为什么这样设计」。🔧 配置模板和部署命令参见 `config/`。📚 软工规范参见 `knowledge/`。🚀 一键部署参见 `deploy/`。
