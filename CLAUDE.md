# CLAUDE.md — Python RAG 项目指令

## 项目身份

- **项目名称**：python-rag（检索增强生成系统）
- **技术栈**：Python 3.12+ / FastAPI / PostgreSQL + pgvector / Redis / LangChain 或 LlamaIndex
- **包管理器**：uv（禁止使用 pip）
- **代码检查**：Ruff（替代 Flake8 + isort）
- **类型检查**：mypy（strict 模式）
- **测试框架**：pytest + pytest-asyncio
- **配置语言**：中文

## 规范遵守

### 编码前必读
1. 编码前必须查阅 `knowledge/` 对应分类文件
2. 涉及 API 设计 → `knowledge/05-编程语言规范/API与接口设计规范.md` + `knowledge/05-编程语言规范/API契约与版本管理规范.md`
3. 涉及 API 安全 → `knowledge/06-安全规范/09-API安全规范.md`
4. 涉及数据库操作 → `knowledge/07-数据库规范/` 对应文件
5. 涉及安全相关 → `knowledge/06-安全规范/` 对应文件
6. 涉及 LLM 调用 → `knowledge/01-Token成本优化/` + `knowledge/02-RAG最佳实践/` + `knowledge/01-Token成本优化/06-Prompt工程规范.md`
7. 涉及可观测性 → `knowledge/03-性能优化/05-可观测性规范.md`
8. 涉及文档创建 → `knowledge/10-软件工程基础/15-文档模板集.md`
9. 涉及协议选型 → `knowledge/10-软件工程基础/16-通信协议选型规范.md`

### 安全红线（Hooks 强制执行，不可绕过）
- 🚫 禁止硬编码 API Key / Secret / Token
- 🚫 禁止直接操作生产数据库
- 🚫 禁止在代码中输出敏感信息到日志
- 🚫 用户输入必须先验证再使用
- 🚫 第三方依赖需检查许可证和安全漏洞
- 🚫 禁止执行不可信代码（必须用 E2B 沙箱）

### Token 成本纪律
- 所有 LLM API 调用默认启用 prompt caching
- 长对话（>50轮）定期触发 compaction
- 模型选择：简单任务用 Haiku 级（deepseek-v4-flash），复杂推理用 Pro 级
- 每次 API 调用前评估：能否用缓存？能否用更小模型？能否合并请求？
- Embedding 结果必须缓存，禁止重复计算

### 推理质量纪律（IMPORTANT — 防止推理退化）

**Read-Before-Edit（MUST）**：
- 修改任何文件前，必须先 Read 该文件及相关依赖
- 不清楚代码上下文时禁止猜测修改，必须搜索确认
- 不被允许的捷径：跳过阅读直接 patch、基于预设假设修改

**两纠错规则（MUST）**：
- 同一问题被用户纠正超过 2 次 → 主动建议 `/clear` 重置上下文
- 重置后用更精确的 prompt 重新出发

**禁止「最简单修复」倾向（MUST）**：
- 方案选择：正确 > 优雅 > 简单。禁止为了改动小而选择有副作用的 hack
- 遇到错误时：先理解根因，再修复。禁止盲目添加 try-catch 吞异常
- 禁止使用的措辞：「minor issue」「edge case」「non-blocking」「acceptable for now」

**约定漂移自检**：
- 长会话（>30 轮）结束前：回顾 CLAUDE.md §规范遵守，确认未偏离

### 代码质量门禁
- 类型注解完整（mypy strict 模式零错误）
- docstring 齐全（Google 风格，中文描述）
- Ruff 零警告
- 单函数 ≤ 50 行，单类 ≤ 500 行
- 圈复杂度 ≤ 10
- 测试覆盖率 ≥ 80%

## 架构约定

### 项目结构
```
src/
├── api/          # FastAPI 路由层（仅处理请求/响应）
├── services/     # 业务逻辑层
├── repositories/ # 数据访问层
├── models/       # 数据模型（Pydantic + SQLAlchemy）
├── core/         # 配置、依赖注入、中间件
└── utils/        # 工具函数
tests/            # 测试（镜像 src/ 结构）
knowledge/        # 项目知识库
docs/             # 文档
```

### 架构原则
- 依赖注入：所有外部依赖通过 FastAPI Depends 注入
- 接口隔离：每个 Service/Repository 定义抽象基类
- 错误处理：统一异常处理中间件，业务异常继承 AppException
- 日志：使用 structlog，JSON 格式输出

## 子代理协作策略

### 模型分级
| 任务复杂度 | 模型 | 子代理类型 |
|-----------|------|-----------|
| 单文件修改、简单问答 | deepseek-v4-flash | Agent (默认) |
| 多文件重构、架构设计 | deepseek-v4-pro | Agent (opus) |
| 并行搜索、批量检查 | deepseek-v4-flash | parallel() |
| 多阶段流水线 | flash + pro 混合 | pipeline() |

### 何时用 parallel vs pipeline

```python
# parallel: 需要所有结果汇总才能继续（如多维度审查后合并报告）
parallel([review_security, review_perf, review_style])

# pipeline: 每个 item 独立流经多阶段（如多文件逐个审查→修复）
pipeline(files, review, fix, verify)

# 默认优先用 pipeline，只有真正需要跨 item 汇总时才用 parallel
```

### 子代理约束
- 子代理默认用 flash 模型（`CLAUDE_CODE_SUBAGENT_MODEL`）
- 需要结构化输出时指定 schema 参数
- 并行文件修改用 worktree 隔离避免冲突
- 子代理不直接回复用户，结果由主代理合成

## 记忆管理（硬性要求，不可跳过）

### 会话开始时（MUST）
1. 读取内置记忆：`~/.claude/projects/D--panzt-projects-claude-code-python-rag/memory/MEMORY.md`
2. 读取项目动态记忆：`./.claude/primer.md`（如存在）
3. 读取当前任务上下文：`./.claude/activeContext.md`（如存在）

### 即时写入触发条件（满足任一立即写，不等到会话结束）
- 🚨 用户做出会影响后续工作的决策（技术选型、架构变更、方向调整）
- 🚨 发现并修复了一个 bug 或配置错误
- 🚨 产生了新的避坑经验或教训
- 🚨 完成了阶段性任务（一个模块、一轮修复、一次验证）
- 🚨 上下文即将压缩（PreCompact hook 触发时）
- **写入方式**：直接调用 Write 工具更新 `.claude/MEMORY.md` 和 `.claude/activeContext.md`，不要等到用户说"结束"

### 每次回复结束前检查（MUST）
在每次回复用户前，评估本轮对话是否产生了需要持久化的信息。如果有，在回复中明确告知用户"📝 已更新记忆文件"，并同时完成写入。

### 知识反馈（避坑归类）
- 验证过的避坑经验应归入 `knowledge/避坑汇总.md` 对应分类
- 每条避坑记录需包含：问题 → 原因 → 解决方案 → 日期
- SessionStart 会提醒未归类的避坑数量

### 会话结束时（用户说"结束"或 Stop Hook 触发）
1. 更新 `.claude/MEMORY.md`：记录本次所有重要决策、错误教训、避坑事项
2. 更新 `.claude/activeContext.md`：当前任务状态、下次会话的上下文
3. 如有架构变更，更新 `.claude/primer.md`
4. 更新 `~/.claude/projects/D--panzt-projects-claude-code-python-rag/memory/MEMORY.md` 索引

## 禁止事项
- 禁止跳过类型检查提交代码
- 禁止使用 `Any` 类型（除非有充分理由并注释说明）
- 禁止裸 except（至少捕获 Exception）
- 禁止在循环中进行数据库查询（使用批量操作）
- 禁止同步 I/O 在 async 函数中（用 asyncio.to_thread 包装）
- 禁止直接拼接 SQL（使用 ORM 或参数化查询）
- 禁止 print() 调试（使用 logger）
- 禁止 import *
