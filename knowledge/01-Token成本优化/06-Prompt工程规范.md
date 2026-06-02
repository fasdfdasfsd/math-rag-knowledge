---
category: Token成本优化
type: spec
priority: must
version: 1.0
updated: 2026-05-30
enforced_by:
  - advisory
---

# Prompt 工程规范

## 一、设计原则

### 结构化优于自由文本
- 使用 XML 标签分隔不同语义块：`<context>`, `<task>`, `<constraints>`, `<output_format>`
- 避免将指令、上下文、示例混杂在同一段落

### TDD 是最强的 Prompt 工程
- 先写测试，再让 AI 生成代码
- 测试即规格，防止 AI "凑正确"
- 禁止 AI 生成验证自身输出的测试

### 渐进式复杂度
- 简单任务：一句话 prompt + 结构化输出 schema
- 中等任务：context + task + constraints + examples
- 复杂任务：分步引导 + 中间验证 + 多轮迭代

## 二、Prompt 模板

### 通用模板
```
<context>
{项目背景、相关文件、已有决策}
</context>

<task>
{单一、明确的任务描述}
</task>

<constraints>
- {约束1}
- {约束2}
</constraints>

<output_format>
{期望的输出格式，JSON Schema 或示例}
</output_format>
```

### 代码生成 Prompt
```
<context>
文件：{file_path}
关联：{related_files}
</context>

<task>实现 {function_name}：{brief_description}</task>

<constraints>
- 类型注解完整，mypy strict 零错误
- 函数 ≤ 50 行
- 遵循 {project_conventions}
</constraints>

<examples>
{正例 + 反例}
</examples>
```

## 三、Prompt 优化策略

| 策略 | 何时用 | 示例 |
|------|--------|------|
| Few-shot | 输出格式难以用 schema 描述 | 提供 2-3 个输入→输出对 |
| Chain-of-Thought | 多步推理任务 | "先分析，再设计，最后实现" |
| 角色设定 | 需要特定视角 | "你是一个安全审计专家" |
| 反例提示 | 常见错误模式 | "不要用 X，因为会导致 Y" |

## 四、缓存感知的 Prompt 设计

### 前缀稳定原则

Prompt 缓存基于前缀匹配——从第一个 token 开始逐字节比对。**任何变化都导致从变化点起全部失效**。

```
✅ 静态内容在前  →  System Prompt → Tools → CLAUDE.md
✅ 动态内容在后  →  会话历史 → 用户最新消息
❌ 时间戳在静态区 →  每次请求前缀不同 → 0% 命中
❌ 工具顺序随机  →  不同请求前缀不同 → 0% 命中
```

### 用消息而非编辑来更新动态信息

```
❌ 修改 system prompt 加"现在是 15:30"→ 缓存全失
✅ 在 user message 末尾加 <system-reminder>现在是 15:30</system-reminder>
```

### CLAUDE.md 设计原则

来自 Anthropic 官方建议：

| 原则 | 说明 |
|------|------|
| **≤ 50 行, ~2,000 tokens** | 作为索引而非完整文档 |
| **不包含动态内容** | 无日期、无本周计划、无变化的值 |
| **指向详细信息位置** | `config: config/index.ts` 而非贴完整配置 |
| **可被压缩后重新加载** | Compaction 后从磁盘重新读取 |

```markdown
# ✅ 好的 CLAUDE.md
## Key Commands
- install: pnpm install
- test: pnpm test

## Code Conventions
- TypeScript strict mode
- API routes in src/api/

## Key Files
- Config: config/index.ts
- Schema: prisma/schema.prisma

## Don't Do
- Don't modify .env.production
```

### 压缩安全提示

在 CLAUDE.md 中加入压缩引导：

```markdown
# Compact Instructions
When compacting, preserve:
- Modified file paths + line numbers
- Test results (pass/fail)
- Active TODO items
- Error messages and stack traces
```

## 五、评估与迭代

- A/B 测试：同一任务用不同 prompt，比较产出质量
- 记录 prompt 性能：token 消耗、产出质量、迭代次数
- 失败的 prompt 也是知识：记录到避坑汇总
- **监控缓存命中率**：prompt 结构变更必须检查是否破坏缓存前缀

## 参考来源

- [Lessons from building Claude Code: Prompt caching is everything (2026.04)](https://claude.com/blog/lessons-from-building-claude-code-prompt-caching-is-everything)
- [Claude Code Prompt Cache 深度解析 — 阿里云 (2026.05)](https://developer.aliyun.com/article/1732421)
