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

## 四、评估与迭代

- A/B 测试：同一任务用不同 prompt，比较产出质量
- 记录 prompt 性能：token 消耗、产出质量、迭代次数
- 失败的 prompt 也是知识：记录到避坑汇总
