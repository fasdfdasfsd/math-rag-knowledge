---
category: Token成本优化
priority: recommended
updated: 2026-05-30
---

# Token 预算与监控

## 概述

建立完善的 token 预算与监控体系，实现对 AI API 调用成本的精细化管控。通过实时计数、成本估算、告警阈值和归因分析，确保 token 消耗在预算范围内，并提供数据支撑的成本优化决策。

## 核心规则

### 🔴 必须遵守 (MUST)

1. **每次 API 调用必须记录 token 消耗**
   - 记录 input_tokens、output_tokens、cache_read_input_tokens、cache_creation_input_tokens
   - 记录关联的模块、功能、用户标识，方便成本归因

2. **设置告警阈值**
   - **WARN（告警）**：单次请求 input + output > 10K tokens
   - **CRITICAL（阻断）**：单次请求 > 100K tokens，需要额外审批
   - 月度 token 消耗超过预算 80% 时触发通知

### 🟡 强烈建议 (SHOULD)

1. **成本估算公式标准化**
   - 总成本 = (input_tokens * input_price + output_tokens * output_price) - saved_cache_tokens * cache_discount
   - 缓存节约 = cache_read_input_tokens * (input_price - cache_read_price)

2. **按模块归因**
   - 每个模块（检索、生成、分类、摘要等）独立记账
   - 定期输出模块级消耗报表

3. **周期性报告**
   - 日报告：前一天的 token 消耗汇总
   - 周报告：趋势分析和异常检测
   - 月报告：预算执行情况和优化建议

### 🟢 可选建议 (MAY)

1. **实时仪表盘**
   - 使用 Grafana 或类似工具展示实时 token 消耗
   - 设置可视化告警面板

2. **自动预算控制**
   - 月度预算耗尽时自动降级模型
   - 超出预算的请求走人工审批队列

## 正确示例

```python
import time
import json
from dataclasses import dataclass, field, asdict
from collections import defaultdict
from datetime import datetime, timedelta
from enum import Enum


class AlertLevel(Enum):
    INFO = "info"
    WARN = "warn"
    CRITICAL = "critical"


@dataclass
class TokenUsage:
    module: str
    feature: str
    model: str
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0
    timestamp: str = ""
    request_id: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()


class Pricer:
    """各模型定价"""
    
    @staticmethod
    def get_price(model: str) -> tuple[float, float, float]:
        """
        返回 (input_price_per_token, output_price_per_token, cache_read_price_per_token)
        示例价格（需与实际合同价格对齐）
        """
        prices = {
            "deepseek-v4-flash":       (1e-6,  2e-6,  0.5e-6),
            "claude-sonnet-4-20250514": (3e-6,  15e-6, 0.3e-6),
            "deepseek-v4-pro":         (15e-6, 75e-6, 1.5e-6),
        }
        return prices.get(model, (3e-6, 15e-6, 0.3e-6))
    
    @classmethod
    def calculate_cost(cls, usage: TokenUsage) -> float:
        input_price, output_price, cache_read_price = cls.get_price(usage.model)
        
        input_cost = usage.input_tokens * input_price
        output_cost = usage.output_tokens * output_price
        cache_saving = usage.cache_read_tokens * (input_price - cache_read_price)
        
        return input_cost + output_cost - cache_saving


class TokenMonitor:
    """Token 消耗监控器"""
    
    def __init__(self):
        self.usages: list[TokenUsage] = []
        self.budget_monthly: float = 100.0  # 月度预算
        self.warn_threshold_per_request: int = 10_000
        self.critical_threshold_per_request: int = 100_000
    
    def record(self, usage: TokenUsage):
        """记录一次 token 消耗"""
        self.usages.append(usage)
        
        total_tokens = usage.input_tokens + usage.output_tokens
        cost = Pricer.calculate_cost(usage)
        
        # 告警检查
        if total_tokens > self.critical_threshold_per_request:
            self._alert(
                AlertLevel.CRITICAL,
                f"单次请求超限: {total_tokens} tokens ({usage.module}/{usage.feature})"
            )
        elif total_tokens > self.warn_threshold_per_request:
            self._alert(
                AlertLevel.WARN,
                f"单次请求较大: {total_tokens} tokens ({usage.module}/{usage.feature})"
            )
        
        print(f"[TokenMonitor] {usage.module}/{usage.feature} | "
              f"in={usage.input_tokens} out={usage.output_tokens} "
              f"cache_read={usage.cache_read_tokens} cost=${cost:.6f}")
    
    def get_module_cost_report(self) -> dict:
        """按模块生成成本报告"""
        module_costs: dict[str, float] = defaultdict(float)
        module_tokens: dict[str, int] = defaultdict(int)
        
        for usage in self.usages:
            cost = Pricer.calculate_cost(usage)
            module_costs[usage.module] += cost
            module_tokens[usage.module] += usage.input_tokens + usage.output_tokens
        
        return {
            module: {
                "cost": round(cost, 4),
                "tokens": module_tokens[module]
            }
            for module, cost in module_costs.items()
        }
    
    def get_daily_report(self) -> dict:
        """生成日报告"""
        today = datetime.utcnow().date()
        today_usages = [
            u for u in self.usages
            if datetime.fromisoformat(u.timestamp).date() == today
        ]
        
        total_cost = sum(Pricer.calculate_cost(u) for u in today_usages)
        total_tokens = sum(u.input_tokens + u.output_tokens for u in today_usages)
        
        return {
            "date": today.isoformat(),
            "total_requests": len(today_usages),
            "total_tokens": total_tokens,
            "total_cost": round(total_cost, 4),
            "module_breakdown": self.get_module_cost_report(),
        }
    
    def get_monthly_report(self) -> dict:
        """生成月度报告"""
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_usages = [
            u for u in self.usages
            if datetime.fromisoformat(u.timestamp) >= month_start
        ]
        
        total_cost = sum(Pricer.calculate_cost(u) for u in month_usages)
        budget_usage_pct = (total_cost / self.budget_monthly) * 100
        
        report = {
            "period": f"{month_start.date()} ~ {datetime.utcnow().date()}",
            "total_requests": len(month_usages),
            "total_cost": round(total_cost, 4),
            "budget": self.budget_monthly,
            "budget_usage_pct": round(budget_usage_pct, 2),
            "module_breakdown": self.get_module_cost_report(),
        }
        
        if budget_usage_pct > 80:
            self._alert(AlertLevel.WARN, f"月度预算已使用 {budget_usage_pct:.1f}%")
        
        return report
    
    def _alert(self, level: AlertLevel, message: str):
        """发送告警"""
        alert_msg = f"[{level.value.upper()}] {message}"
        print(alert_msg)
        if level == AlertLevel.CRITICAL:
            # 实际应接入告警系统（如 Slack、邮件、PagerDuty）
            pass
```

## 错误示例

```python
# 错误 1：不记录任何 token 消耗
def bad_no_tracking():
    """
    没有监控 → 月底发现账单爆炸
    无法追溯是哪段代码/哪个功能花的多
    无法优化成本
    """

# 错误 2：只记录总量，不按模块归因
def bad_no_attribution():
    """只记录了总 token 数，没有模块信息"""
    log_entry = {
        "date": "2026-05-30",
        "total_tokens": 1_500_000,
        # 缺少 module/feature 维度
        # 无法知道是检索模块还是生成模块花的多
    }


# 错误 3：没有告警阈值
def bad_no_alerts():
    """没有设置告警，直到成本失控"""
    # 一个 bug 导致循环调用 API
    # 单次请求 500K tokens
    # 没有告警 → 持续运行直到预算耗尽
    while True:
        response = client.messages.create(
            model="deepseek-v4-pro",
            max_tokens=100000,
            messages=[{"role": "user", "content": "x" * 50000}]
        )
        # 永远不会被告知


# 错误 4：手动估算成本
def bad_manual_estimate():
    """手动估算，容易出错"""
    monthly_tokens = 50_000_000
    # 错误公式：忽略 output 和 cache 的区别
    estimated_cost = monthly_tokens * 3e-6  # 不准确
    # 应使用标准的成本估算公式
```

## 工具链配置

```python
# tiktoken 实时 token 计数
import tiktoken

def count_tokens_for_request(text: str, model: str = "claude-sonnet-4-20250514") -> int:
    """在发送请求前估算 token 数"""
    try:
        enc = tiktoken.encoding_for_model(model)
    except KeyError:
        enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))

# 预算检查中间件
class BudgetMiddleware:
    """请求前检查预算是否耗尽"""
    
    def __init__(self, monitor: TokenMonitor):
        self.monitor = monitor
    
    async def check_budget(self, estimated_tokens: int) -> bool:
        report = self.monitor.get_monthly_report()
        if report["budget_usage_pct"] >= 100:
            print("[Budget] 预算已耗尽，请求被阻断")
            return False
        return True
```

## 进阶专题

### Claude Code 内置监控命令

| 命令 | 功能 | 输出 |
|------|------|------|
| `/cost` | 显示累计 token 和费用 | 按模型/会话分摊 |
| `/context` | 显示 token 使用明细 | 彩色网格：系统/工具/MCP/对话 |
| `/usage` | API 套餐上限和速率限制 (v2.1.70+) | 剩余额度/重置时间 |

### 缓存命中率监控（SEV 级别）

Anthropic 将缓存命中率当事故监控。应建立：

```python
# 每请求检查缓存效率
ideal: cache_read_input_tokens >> input_tokens
alert: cache_read_input_tokens / total_input < 0.5  # 低于 50% 命中率告警
```

优化后目标：**92%** 缓存命中率，有效成本仅无缓存的 **~16%**。

### 三层成本优化体系

| 层 | 机制 | 节省 |
|:--:|------|:--:|
| **Layer 1** | Anthropic 原生 prompt caching | 68% 命中 |
| **Layer 2** | 语义缓存 (cosine ≥ 0.95 复用) | 15% 命中 |
| **Layer 3** | 结果缓存 (Redis 智能 TTL) | 10% 命中 |

三层叠加 → **93% 综合命中率**，月成本从 $47K → $2.8K。

### 关键指标看板

| 指标 | 目标 | 告警阈值 |
|------|:--:|:--:|
| 缓存命中率 | > 80% | < 50% |
| 无效缓存写入 | < 5% | > 10% |
| 模型降级率 (pro→sonnet) | < 20% | > 40% |
| 单请求 token | < 10K | > 100K |
| 月度预算使用率 | < 80% | > 90% |

### 参考来源

- [Anthropic API Usage](https://docs.anthropic.com/en/api/usage)
- [Using Claude Code: session management and 1M context (2026.04)](https://claude.com/blog/using-claude-code-session-management-and-1m-context)
- [How We Cut LLM API Costs by 94%: A 3-Layer Caching Strategy — dev.to](https://dev.to/anilatambharii/how-we-cut-llm-api-costs-by-94-a-3-layer-caching-strategy-145l)
- [tiktoken 官方文档](https://github.com/openai/tiktoken)
