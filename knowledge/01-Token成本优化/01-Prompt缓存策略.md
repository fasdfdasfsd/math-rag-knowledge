---
category: Token成本优化
priority: must
updated: 2026-05-30
---

# Prompt 缓存策略

## 概述

Prompt Caching 是 Anthropic API 提供的一项优化功能，通过在 prompt 中设置 `cache_control` 断点标记，使得相同前缀内容在 TTL（5分钟）内复用缓存结果，大幅降低 token 消耗和延迟。该功能对包含大量静态内容（system prompt、工具定义、few-shot 示例）的请求尤其有效。

## 核心规则

### 🔴 必须遵守 (MUST)

1. **所有 system prompt 必须标记为缓存断点**
   - 将完整的 system prompt 放在 messages 数组之前，使用 `cache_control={"type": "ephemeral"}` 标记
   - 确保 system prompt 在不同请求之间保持完全一致（包括空格、换行）

2. **工具定义（tools）必须标记为缓存断点**
   - tools 参数中的全部工具定义设置 `cache_control={"type": "ephemeral"}`
   - 工具定义变更后会自动重建缓存

3. **缓存前缀必须完全一致**
   - 缓存匹配基于字节级别的前缀匹配，任何细微差异都会导致缓存未命中
   - 请求中位于 `cache_control` 断点之前的所有内容都会被缓存

4. **监控缓存效率指标**
   - 读取 `response.usage.cache_read_input_tokens` 确认缓存命中
   - 读取 `response.usage.cache_creation_input_tokens` 确认缓存创建
   - 缓存命中率目标：**> 80%**

### 🟡 强烈建议 (SHOULD)

1. **将静态内容前置，动态内容后置**
   - 静态 system prompt、工具定义放在 messages 数组前部
   - 用户提问、动态上下文放在缓存断点之后
   - 避免在缓存前缀区域插入会话级别的动态内容

2. **缓存预热策略**
   - 服务启动后，立即发送一个带缓存标记的预热请求
   - 预热请求 body 可以任意，但前缀（static content）必须与真实请求一致

3. **TTL 管理**
   - 缓存 TTL 为 5 分钟（从最后一次访问刷新）
   - 高并发场景下，确保请求间隔不超过 5 分钟
   - 低频场景可考虑定期发送 keep-alive 请求维持缓存

### 🟢 可选建议 (MAY)

1. **多级缓存断点**
   - 对超长 prompt 可在多个位置设置缓存断点（需成本效益分析）
   - 二级断点适用于：公共示例 + 私有上下文 的场景

2. **缓存降级策略**
   - 缓存未命中时应有降级逻辑，不影响用户响应

## 正确示例

```python
import anthropic

client = anthropic.Anthropic()

# 正确：system prompt 和 tools 标记缓存断点
system_prompt = (
    "你是一个专业的 Python 开发助手，擅长编写高质量的 Python 代码。"
    "你熟悉 FastAPI、Pydantic、SQLAlchemy 等现代 Python 框架。"
    "回答时请提供完整的可运行代码示例。"
)

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=4096,
    # system 参数中设置缓存断点
    system=[
        {
            "type": "text",
            "text": system_prompt,
            "cache_control": {"type": "ephemeral"}
        }
    ],
    # tools 参数中设置缓存断点
    tools=[
        {
            "name": "search_code",
            "description": "搜索代码库中的相关代码片段",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                }
            },
            "cache_control": {"type": "ephemeral"}
        }
    ],
    messages=[
        {"role": "user", "content": "请帮我实现一个 FastAPI 用户注册接口"}
    ]
)

# 监控缓存效果
print(f"缓存读取 Token: {response.usage.cache_read_input_tokens}")
print(f"缓存创建 Token: {response.usage.cache_creation_input_tokens}")
print(f"输入 Token: {response.usage.input_tokens}")
print(f"输出 Token: {response.usage.output_tokens}")

# 计算缓存命中率
if response.usage.cache_read_input_tokens > 0:
    hit_ratio = response.usage.cache_read_input_tokens / (
        response.usage.cache_read_input_tokens + response.usage.cache_creation_input_tokens
    )
    print(f"缓存命中率: {hit_ratio:.1%}")
```

## 错误示例

```python
import anthropic
from typing import List

client = anthropic.Anthropic()

# 错误 1：动态内容放在缓存断点前，导致缓存失效
def bad_caching_1(user_query: str, conversation_history: List[dict]):
    messages = []
    # 错误：将动态内容（对话历史）拼接到缓存前缀之前
    for msg in conversation_history:  # conversation_history 每次请求不同
        messages.append(msg)
    
    messages.append({
        "role": "user",
        "content": user_query
    })
    
    # 此时 system prompt 前的历史记录不断变化，缓存永远无法命中
    return client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=[
            {
                "type": "text",
                "text": "你是一个 Python 助手",
                "cache_control": {"type": "ephemeral"}
            }
        ],
        messages=messages
    )

# 错误 2：忘记设置 cache_control
def bad_caching_2():
    # 没有缓存标记，每次请求都重新计算
    return client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=[
            {
                "type": "text",
                "text": "你是一个 Python 助手"
                # 缺少 cache_control 参数
            }
        ],
        messages=[
            {"role": "user", "content": "你好"}
        ]
    )

# 错误 3：每次请求修改 system prompt（即使微小的差异）
def bad_caching_3(date_str: str):
    # 每次插入日期，导致 system prompt 不同
    system_text = f"今天是 {date_str}。你是一个 Python 助手。"
    return client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=[
            {
                "type": "text",
                "text": system_text,  # 日期变化 → 缓存未命中
                "cache_control": {"type": "ephemeral"}
            }
        ],
        messages=[
            {"role": "user", "content": "你好"}
        ]
    )
```

## 工具链配置

```python
# 缓存监控中间件示例
import time
from dataclasses import dataclass, field
from collections import defaultdict

@dataclass
class CacheMetrics:
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    total_tokens_saved: int = 0
    
    def record(self, usage):
        self.total_requests += 1
        if usage.cache_read_input_tokens > 0:
            self.cache_hits += 1
            self.total_tokens_saved += usage.cache_read_input_tokens
        elif usage.cache_creation_input_tokens > 0:
            self.cache_misses += 1
    
    @property
    def hit_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.cache_hits / self.total_requests

# 全局缓存指标
cache_metrics = CacheMetrics()
```

## 参考来源

- [Anthropic Prompt Caching 文档](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching)
- [Anthropic Cache Usage API Reference](https://docs.anthropic.com/en/api/creating-messages#usage)
