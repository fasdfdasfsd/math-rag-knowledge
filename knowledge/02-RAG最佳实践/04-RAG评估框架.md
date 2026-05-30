---
category: RAG最佳实践
priority: recommended
updated: 2026-05-30
---

# RAG 评估框架

## 概述

建立系统化的 RAG 评估体系，涵盖自动评估指标和人工评估流程。使用 RAGAS 框架的核心指标对检索质量与生成质量进行量化评估，确保 RAG 系统的持续改进。

## 核心规则

### 🔴 必须遵守 (MUST)

1. **每次迭代都必须运行评估 pipeline**
   - 任何分块策略、检索参数、prompt 修改后必须重新评估
   - 评估结果作为是否发布到生产的判断依据

2. **评估数据集必须包含边界情况**
   - 包含：短查询、长查询、模糊查询、专业术语查询
   - 包含：无答案查询（预期模型应拒绝回答）

### 🟡 强烈建议 (SHOULD)

1. **使用 RAGAS 四项核心指标**
   - **Faithfulness（忠实度）**：生成内容是否基于检索结果，不编造事实
   - **Answer Relevancy（答案相关性）**：生成内容是否回答了问题
   - **Context Precision（上下文精确度）**：检索结果中相关文档的占比
   - **Context Recall（上下文召回率）**：所需信息是否都被检索到

2. **自动化评估 pipeline**
   - 集成到 CI/CD 流程
   - 评估结果与基线对比，退化 > 5% 则阻断发布

3. **人工评估 checklist**
   - 信息准确性：是否有事实错误
   - 引用完整性：是否标注了信息来源
   - 语言质量：是否通顺、符合预期风格

### 🟢 可选建议 (MAY)

1. **A/B 测试**
   - 同时在线的两个版本进行对比评估
   - 收集用户隐式反馈（点击、停留时间）

2. **维度专项评估**
   - 针对性评估：多轮对话、跨文档推理、多语言等

## 正确示例

```python
from typing import List, Dict, Any
from dataclasses import dataclass, field
import json
import numpy as np


@dataclass
class EvaluationSample:
    question: str
    ground_truth: str
    retrieved_contexts: List[str] = field(default_factory=list)
    generated_answer: str = ""
    
    # RAGAS 指标分数
    faithfulness: float = 0.0
    answer_relevancy: float = 0.0
    context_precision: float = 0.0
    context_recall: float = 0.0


class RAGASEvaluator:
    """RAGAS 指标评估器"""
    
    def __init__(self, llm_client):
        self.llm = llm_client
    
    async def evaluate_faithfulness(self, question: str, answer: str, 
                                     contexts: List[str]) -> float:
        """
        评估忠实度：生成内容是否基于检索结果
        从答案中提取陈述，检查每个陈述是否能被检索结果支持
        """
        prompt = f"""评估下面答案的忠实度（0-1分）。
忠实度衡量答案中的每个陈述是否都能从给定的上下文中找到依据。

上下文：
{" ".join(contexts[:3])}

问题：{question}
答案：{answer}

请返回一个 0-1 之间的分数：
- 1.0：答案中的所有陈述都可以从上下文中找到直接依据
- 0.5：答案中部分陈述没有上下文依据
- 0.0：答案几乎完全编造，与上下文无关

只返回数字，不要有其他文字。"""
        
        response = await self.llm.generate(prompt)
        try:
            return float(response.strip())
        except ValueError:
            return 0.5
    
    async def evaluate_answer_relevancy(self, question: str, 
                                         answer: str) -> float:
        """
        评估答案相关性：生成内容是否回答了问题
        """
        prompt = f"""评估下面答案的相关性（0-1分）。
相关性衡量答案是否直接回答了问题。

问题：{question}
答案：{answer}

请返回一个 0-1 之间的分数：
- 1.0：答案直接、完整地回答了问题
- 0.5：答案部分相关，但没有完全回答问题
- 0.0：答案与问题完全无关

只返回数字，不要有其他文字。"""
        
        response = await self.llm.generate(prompt)
        try:
            return float(response.strip())
        except ValueError:
            return 0.5
    
    async def evaluate_context_precision(self, question: str, 
                                          contexts: List[str]) -> float:
        """
        评估上下文精确度：检索结果中相关文档的比例
        """
        if not contexts:
            return 0.0
        
        relevant_count = 0
        for ctx in contexts:
            prompt = f"""判断以下上下文是否与问题相关（回答 yes/no）：

问题：{question}
上下文：{ctx[:500]}"""
            response = await self.llm.generate(prompt)
            if response.strip().lower().startswith("yes"):
                relevant_count += 1
        
        return relevant_count / len(contexts)
    
    async def evaluate_context_recall(self, question: str, 
                                       ground_truth: str,
                                       contexts: List[str]) -> float:
        """
        评估上下文召回率：回答所需的信息是否都被检索到
        """
        # 从 ground_truth 中提取关键信息点
        claims_prompt = f"""从下面的标准答案中提取关键信息点（每行一个）：

标准答案：{ground_truth}

输出格式（每行一个）：
- 信息点1
- 信息点2
..."""
        
        claims_response = await self.llm.generate(claims_prompt)
        claims = [c.strip("- ").strip() for c in claims_response.split("\n") if c.strip()]
        
        # 检查每个信息点在上下文中是否存在
        supported = 0
        for claim in claims:
            support_prompt = f"""判断以下信息点是否能在给定上下文中找到支持（回答 yes/no）：

信息点：{claim}
上下文：{" ".join(contexts[:3])[:1000]}"""
            
            response = await self.llm.generate(support_prompt)
            if response.strip().lower().startswith("yes"):
                supported += 1
        
        return supported / len(claims) if claims else 0.0
    
    async def evaluate_sample(self, sample: EvaluationSample) -> EvaluationSample:
        """评估单个样本的所有指标"""
        sample.faithfulness = await self.evaluate_faithfulness(
            sample.question, sample.generated_answer, sample.retrieved_contexts
        )
        sample.answer_relevancy = await self.evaluate_answer_relevancy(
            sample.question, sample.generated_answer
        )
        sample.context_precision = await self.evaluate_context_precision(
            sample.question, sample.retrieved_contexts
        )
        sample.context_recall = await self.evaluate_context_recall(
            sample.question, sample.ground_truth, sample.retrieved_contexts
        )
        return sample


class EvaluationPipeline:
    """完整评估 Pipeline"""
    
    def __init__(self, evaluator: RAGASEvaluator, baseline_path: str | None = None):
        self.evaluator = evaluator
        self.baseline: dict | None = None
        if baseline_path:
            with open(baseline_path) as f:
                self.baseline = json.load(f)
    
    async def run(self, samples: List[EvaluationSample]) -> dict:
        """运行完整评估"""
        results = []
        for i, sample in enumerate(samples):
            print(f"[Evaluation] 评估样本 {i+1}/{len(samples)}")
            result = await self.evaluator.evaluate_sample(sample)
            results.append(result)
        
        # 汇总指标
        summary = {
            "num_samples": len(results),
            "faithfulness": np.mean([r.faithfulness for r in results]),
            "answer_relevancy": np.mean([r.answer_relevancy for r in results]),
            "context_precision": np.mean([r.context_precision for r in results]),
            "context_recall": np.mean([r.context_recall for r in results]),
            "overall_score": np.mean([
                r.faithfulness + r.answer_relevancy + 
                r.context_precision + r.context_recall
            for r in results]) / 4,
        }
        
        # 与基线对比
        if self.baseline:
            summary["baseline_comparison"] = {}
            for metric in ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]:
                diff = summary[metric] - self.baseline.get(metric, 0)
                summary["baseline_comparison"][metric] = round(diff, 4)
                if diff < -0.05:  # 退化超过 5%
                    print(f"[ALERT] {metric} 退化 {diff:.1%}，超过 5% 阈值！")
        
        return summary
    
    @staticmethod
    def print_report(summary: dict):
        """打印评估报告"""
        print("\n" + "=" * 50)
        print("RAG 评估报告")
        print("=" * 50)
        print(f"样本数量: {summary['num_samples']}")
        print(f"\n核心指标:")
        print(f"  Faithfulness:        {summary['faithfulness']:.3f}")
        print(f"  Answer Relevancy:    {summary['answer_relevancy']:.3f}")
        print(f"  Context Precision:   {summary['context_precision']:.3f}")
        print(f"  Context Recall:      {summary['context_recall']:.3f}")
        print(f"  Overall Score:       {summary['overall_score']:.3f}")
        
        if "baseline_comparison" in summary:
            print(f"\n与基线对比:")
            for metric, diff in summary["baseline_comparison"].items():
                status = "👍" if diff >= 0 else "👎"
                print(f"  {metric:25s}: {diff:+.4f} {status}")
        print("=" * 50)
```

## 错误示例

```python
# 错误 1：只用自动指标，没有人工评估
def bad_auto_only():
    """自动评估可能忽略语义层面的问题"""
    
    # 场景：评估数据集只有 10 个简单问题
    # 自动指标全部 > 0.9
    # 但真实用户场景中发现：
    # - 专业术语回答有误（自动评估无法发现）
    # - 代码示例有 bug（自动评估无法发现）
    # - 引用的文档版本错误（自动评估无法发现）


# 错误 2：评估数据集太小或太偏
def bad_small_dataset():
    """只有 5 个样本，且都是简单查询"""
    samples = [
        EvaluationSample("FastAPI 是什么？", "FastAPI 是一个 Web 框架"),
        EvaluationSample("Python 是什么？", "Python 是一种编程语言"),
        # ... 都是简单定义问题
    ]
    # 评估结果高，但实际场景中复杂查询表现差


# 错误 3：不同版本间评估条件不一致
def bad_inconsistent_eval():
    """评估条件不同导致结果不可比"""
    
    # v1 评估：使用 LLM 评估器 A，数据集 dataset_v1
    # v2 评估：使用 LLM 评估器 B，数据集 dataset_v2
    # → 结果无法直接对比
    # 应固定评估器版本和评估数据集


# 错误 4：忽略无答案查询
def bad_no_unanswerable():
    """评估数据集中没有包含"无答案"场景"""
    
    samples = [
        # 所有问题都能在知识库中找到答案
        EvaluationSample("FastAPI 路由怎么定义", "..."),
        EvaluationSample("Python 装饰器是什么", "..."),
    ]
    # 没有测试：知识库中不存在答案时，模型是否合理拒绝
    # 否则模型可能在无法回答时仍然编造答案
```

## 工具链配置

```python
# 人工评估 Checklist
HUMAN_EVALUATION_CHECKLIST = """
## 人工评估 Checklist
评估人: __________  日期: __________  样本 ID: __________

### 信息准确性
- [ ] 所有事实陈述准确无误
- [ ] 代码示例可以正确运行
- [ ] 数据引用来源正确

### 引用完整性
- [ ] 重要声明有来源标注
- [ ] 引用格式正确
- [ ] 引用内容与上下文一致

### 语言质量
- [ ] 语言通顺，符合预期风格
- [ ] 专业术语使用正确
- [ ] 格式整洁（代码块、标题、列表）

### 安全合规
- [ ] 无敏感信息泄露
- [ ] 无偏见或歧视性内容
- [ ] 符合内容安全策略

### 综合评分（1-5）
- 整体满意度：___ / 5
- 检索质量：___ / 5
- 生成质量：___ / 5

### 问题反馈
_______
"""
```

## 参考来源

- [RAGAS 官方文档](https://docs.ragas.io/)
- [RAG Evaluation Guide](https://www.pinecone.io/learn/rag-evaluation/)
