# primer.md — 项目架构约定

> 最后更新: 2026-06-02 ~02:00
> 性质: 动态记忆层，随架构变更更新

## 项目身份

- **项目名称**：math-rag-knowledge（数学学习 RAG 知识库管理应用）
- **技术栈**：Python 3.12+ / FastAPI / Milvus / PostgreSQL / Redis / DeepSeek / MinerU
- **包管理器**：uv（禁止 pip）
- **代码检查**：Ruff（替代 Flake8 + isort）
- **类型检查**：mypy（strict 模式）
- **测试框架**：pytest + pytest-asyncio

## 架构决策记录

### ADR-001: 分层架构
- API 层（FastAPI 路由）→ Service 层（业务逻辑）→ Repository 层（数据访问）
- 所有外部依赖通过 FastAPI Depends 注入
- 每层定义抽象基类
- 新增 **Document Pipeline 层**：独立的文档处理流水线（MinerU 解析 → Chunking → Embedding）

### ADR-002: 向量数据库选型
- **主选**：Milvus（大规模向量检索，支持 10 亿级向量）
- **辅助**：PostgreSQL + pgvector（关系数据与向量并存的小规模场景）
- 选型理由：数学知识库可能包含大量公式、题目、解题步骤的向量化存储，Milvus 的原生 HNSW/IVF 索引和分布式能力更适合

### ADR-003: RAG 框架
- **自定义实现**（不依赖 LangChain/LlamaIndex 重量框架）
- Embedding：DeepSeek Embedding API（兼容 OpenAI SDK）
- 向量存储：pymilvus（Milvus 原生 Python SDK）
- 检索策略：语义检索 + 重排序（Rerank）两阶段
- 生成：DeepSeek Chat API（兼容 OpenAI SDK）
- 选型理由：轻量可控，避免框架耦合，数学领域的 Chunking 和检索需要定制化

### ADR-004: 文档解析引擎
- **主选**：MinerU（PDF/图片 → Markdown + LaTeX 公式）
- 数学公式感知：MinerU 原生支持 LaTeX 公式提取
- 备选：Unstructured（通用文档解析，但对中文数学公式支持较弱）

### ADR-005: 大模型
- **主选**：DeepSeek（兼容 OpenAI SDK，国产，性价比高）
- Chat 模型：deepseek-chat（日常对话和推理）
- Embedding 模型：deepseek-embedding（或通过 API 获取的对应模型）
- 备选：通义千问 / 智谱 GLM（如果 DeepSeek 不可用）

### ADR-006: 记忆管理
- 静态层 CLAUDE.md → 动态层 primer.md + activeContext.md → 自动层 MEMORY.md
- 三钩防丢失：PreCompact / Stop / SessionStart
- 即时写入触发条件：决策 / bug修复 / 避坑 / 阶段完成 / PreCompact

### ADR-007: 软件工程流程与多角色协作框架
- **决策**：所有软件工程类项目严格遵循 `knowledge/08-软件工程生命周期/` 11 阶段流程
- **10 角色 RASCI 矩阵**：PO / Arch / TL / SecEng / QA / DevOps / DBA / Dev / SRE / PM
- **Claude Code 多角色协作**：子代理模拟角色 persona，每阶段启动对应角色审查
- **决策权限三级**：自主决策 / 建议+执行 / 选择题决策
- **沟通规则**：需要用户决策时只出选择题不出问答题；反对意见必须提；先理解再回应
- **阶段准出条件**：每阶段必须完成 knowledge/ 规范中定义的 checklist 方可进入下一阶段
- 详情见 `CLAUDE.md §软件工程流程纪律` 和 `§多角色协作框架`

### ADR-008: 多智能体强制协作规程
- **决策**：每个软件工程阶段必须启动 ≥ 3 个独立智能体并行分析，达成共识后才能向用户汇报
- **6 条强制规则**（M-1~M-5 + 反模式）：独立工作、共识优先、未共识不汇报、分歧升级
- **10 阶段智能体配置模板**：每阶段指定 R/S/C 三角色智能体 + 可选第 4 智能体
- **5 步共识流程**：分解→并行→比对→辩论→汇报
- 详情见 `CLAUDE.md §多智能体强制协作规程`

### ADR-009: 核心智能体管家（Orchestrator）
- **决策**：增设全局元角色"核心智能体管家"，由主会话 Claude 担任，不参与业务分析，只做管理调度
- **8 项职责**：阶段调度/智能体派遣/进度跟踪/共识裁决/容错处理/上下文监控/用户汇报/记忆持久化
- **5 种容错策略**：单智能体重试/多智能体暂停/格式异常修复/上下文强制压缩/API 不可用降级
- **进度量化标准**：11 阶段加权百分比公式
- 详情见 `CLAUDE.md §核心智能体管家`

### ADR-010: 产品治理规则体系
- **决策**：建立覆盖 6 大领域 70+ 条规则的产品治理体系
- **6 大领域**：产品价值观（10条）/ 内容创作红线（22条）/ 儿童安全防护（17条）/ AI伦理（9条）/ 数学教育（6条）/ 商业伦理（6条）
- **三级强制执行**：🔴红线（代码层阻断）→ 🟡强约束（后置校验不通过→重生成）→ 🟢指导原则（人工抽检）
- **四层执行架构**：Pre-LLM消毒 → System Prompt硬约束 → Post-LLM审核 → 人工抽检兜底
- **法规依据**：中国《生成式AI安全指引》(2025.6) + 《AI伦理规范共识》(2025.9) + 美国 CARU 风险矩阵 (2025.10) + COPPA 2025 + PBS + UNICEF
- 详情见 `docs/产品治理规则-数学冒险世界-v1.md` 和 `CLAUDE.md §产品治理红线`

### ADR-011: LLMProvider ABC + 工厂注册模式
- **决策**：定义 LLMProvider 抽象基类（5 个抽象方法），通过工厂模式运行时注册/切换
- **理由**：降低 DeepSeek API 不可用风险，支持通义千问/智谱 GLM 热切换
- **实现**：`src/services/llm_generation/llm_provider.py` — ABC + DeepSeekProvider 具体实现
- **5 个抽象方法**：generate / generate_stream / embed / count_tokens / check_health

### ADR-012: 一次生成 6 段 → 逐段校验 → 逐段 SSE
- **决策**：LLM 一次生成完整 6 段冒险叙事，后端逐段校验后逐段 SSE 推送
- **理由**：避免 6 次独立 LLM 调用（成本 ×6 + 延迟累加），单次生成保持叙事连贯性
- **约束**：P95 首段 < 3s，全部 6 段 P95 < 60s
- **降级**：LLM 超时 → 模板替换；校验失败 → 安全模板

### ADR-013: Background Worker + PostgreSQL 关卡预生成池
- **决策**：Background Worker 预生成关卡存入 PostgreSQL，命中率 ≥ 60%
- **理由**：解决 500 并发 LLM 生成瓶颈
- **参数**：池大小 50-100，TTL 6h
- **实现**：`src/services/pregen_pool/` + `src/workers/pregen_scheduler.py`

### ADR-014: 重生成限制修正（3 → 1 次）
- **决策**：SRS v2.1 写"最多 3 次"修正为"最多 1 次，失败 → 安全模板"
- **理由**：P95 < 60s 下 3 次 LLM 调用不可行（单次 ~20s）
- **实现**：ContentSafetyValidator 重试 1 次后直接使用模板库替换

### ADR-015: 浏览器 EventSource + fetch 降级方案
- **决策**：MVP 用 EventSource，发现不支持自定义 Header → 切换到 fetch + ReadableStream
- **理由**：SSE 认证需要 Authorization header，EventSource API 不支持
- **实现**：`frontend/src/stores/adventureStore.ts` — fetch + getReader + 手动解析 SSE

### ADR-016: 行为宪法配置固化
- **决策**：用户反复强调的 4 条行为红线写入 3 层配置文件，会话启动自动加载
- **4 条红线**：①决策=选择题+推荐 ②无人值守=不问确认 ③上下文≥75%警告 ④≥3 智能体共识后汇报
- **3 层配置**：`.claude/rules/behavior.md` + `.claude/rules/autonomous.md` + `settings.json` SessionStart
- **全局覆盖**：`~/.claude/CLAUDE.md` 顶部引用
- **理由**：同一会话中多次纠正相同行为模式 → 需配置级固化防止遗忘

### ADR-SEC-001: Pre/Post-LLM 双端审核架构
- **决策**：学生输入进 LLM 前消毒，LLM 输出到用户前审核
- **理由**：单端无法覆盖所有风险（输入绕过 + 输出幻觉）
- **替代方案**：仅 Post-LLM 审核（不充分，注入攻击无法防范）
- **实现**：Pre-LLM（红线规则 + 注入检测 + PII 脱敏）→ LLM → Post-LLM（敏感词 + 安全分类 + 禁止表述 + 课标超纲）
- 详情见 `docs/安全架构设计-数学冒险世界-v1.md` §5.2~§5.3

### ADR-SEC-002: 确定性规则引擎为主，LLM 审核为辅
- **决策**：内容安全审核以确定性规则引擎（关键词+正则+N分类器）为主，LLM 审核仅用于人工审核辅助
- **理由**：规则引擎确定性高、延迟低（<10ms）、无循环依赖
- **限制**：LLM 审核仅用于"指导原则"级别的人工抽检
- **实现**：治理规则引擎 (RedLineRuleEngine) + 注入检测分类器 (ONNX Runtime, <50MB)

### ADR-SEC-003: 审计日志链式哈希
- **决策**：采用 HMAC 链式哈希结构确保审计日志不可篡改
- **理由**：满足合规审计的"不可篡改"要求
- **替代方案**：区块链（太重，不需要去中心化）
- **实现**：每笔日志记录 prev_hash + 自身 data → HMAC-SHA256 计算当前 hash，日终归档最终 hash 到独立见证表

### ADR-SEC-004: 年龄验证最小 PII
- **决策**：分 4 级验证（L0 自声明 → L1 邮箱 → L2 支付验证 → L3 正式认证）
- **理由**：不阻塞首次体验，同时满足 COPPA 2025 要求
- **设计约束**：6-8 岁最低保护等级，12-14 岁可适当放宽
- **实现**：首次注册仅选择年龄区间（不要求精确出生日期）→ 填写家长邮箱即可开始使用

### ADR-SEC-005: 种子库 + Fuzzing 双保险
- **决策**：手动种子库（54 条）+ 自动变异生成（每季度 50+ 条）
- **理由**：手工确保覆盖已知攻击面，自动变异覆盖未知变体
- **验证标准**：突破率 < 1%
- **实现**：种子库分类管理（PI/PII/IC/EM/SB/PR/HB/MS/CA）+ CI Stage 4 自动执行 + 报告驱动

### ADR-SEC-006: 安全审核独立部署
- **决策**：内容安全审核服务独立 Docker container 部署
- **理由**：安全审计的隔离性和可靠性要求（一个进程崩溃不影响审核）
- **实现**：独立 container + 独立资源限制 + 健康检查

## 关键约定

- 类型注解完整（mypy strict 零错误）
- docstring 齐全（Google 风格，中文）
- 单函数 ≤ 50 行，单类 ≤ 500 行
- 禁止裸 except、禁止 Any 类型、禁止循环中数据库查询
- 禁止 print() 调试，使用 structlog
- Embedding 结果必须缓存（Redis）
- 所有 LLM 调用启用 prompt caching
