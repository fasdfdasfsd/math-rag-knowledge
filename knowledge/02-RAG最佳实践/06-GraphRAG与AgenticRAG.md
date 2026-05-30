---
category: RAG最佳实践
priority: optional
updated: 2026-05-30
---

# GraphRAG 与 Agentic RAG

## 概述

GraphRAG 通过知识图谱增强检索的结构化理解能力，Agentic RAG 通过多步推理和工具调用实现复杂的自主检索。本规范介绍两种高级 RAG 范式的核心概念、实现模式和适用场景。

## 核心规则

### 🔴 必须遵守 (MUST)

1. **GraphRAG 必须有实体识别和关系抽取**
   - 从文档中提取命名实体及其关系
   - 构建知识图谱的节点和边

2. **Agentic RAG 必须有明确的终止条件**
   - 设置最大推理步数
   - 设置超时时间
   - 定义"足够回答"的判定标准

### 🟡 强烈建议 (SHOULD)

1. **GraphRAG 社区摘要策略**
   - 对密集连接的实体群组生成社区摘要
   - 社区摘要作为高层级检索单元

2. **Agentic RAG 的 Router/Retriever/Reader 模式**
   - Router：分析查询意图，选择检索策略
   - Retriever：执行具体检索操作
   - Reader：综合结果生成回答

3. **适用场景判断**
   - GraphRAG 适合：多跳推理、关系查询、全局性理解
   - Agentic RAG 适合：复杂问题分解、需要多步推理
   - 传统 RAG 仍适合：简单 Q&A、单文档检索

### 🟢 可选建议 (MAY)

1. **混合架构**
   - 向量检索 + 图谱检索双通道
   - Agent 根据查询类型选择通道

2. **动态图谱更新**
   - 新文档入库时增量更新知识图谱
   - 关系权重动态调整

## 正确示例

```python
from typing import List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
import re


# ========== GraphRAG 实现 ==========

@dataclass
class Entity:
    name: str
    type: str           # "person", "technology", "concept", ...
    description: str
    source_docs: List[str] = field(default_factory=list)

@dataclass
class Relation:
    source: str
    target: str
    relation_type: str  # "uses", "depends_on", "part_of"...
    weight: float = 1.0


class KnowledgeGraph:
    """知识图谱"""
    
    def __init__(self):
        self.entities: dict[str, Entity] = {}
        self.relations: List[Relation] = []
    
    def add_entity(self, entity: Entity):
        if entity.name not in self.entities:
            self.entities[entity.name] = entity
        else:
            # 合并信息
            existing = self.entities[entity.name]
            existing.description += "; " + entity.description
            existing.source_docs.extend(entity.source_docs)
    
    def add_relation(self, relation: Relation):
        self.relations.append(relation)
    
    def get_community_summary(self, entity_name: str, depth: int = 2) -> str:
        """生成实体周围深度 depth 的社区摘要"""
        visited = set()
        community_entities = set()
        community_relations = []
        
        def dfs(current: str, d: int):
            if d > depth or current in visited:
                return
            visited.add(current)
            if current in self.entities:
                community_entities.add(current)
                for rel in self.relations:
                    if rel.source == current:
                        community_relations.append(rel)
                        dfs(rel.target, d + 1)
                    elif rel.target == current:
                        community_relations.append(rel)
                        dfs(rel.source, d + 1)
        
        dfs(entity_name, 0)
        
        summary_parts = [
            f"实体: {entity_name}",
            f"类型: {self.entities.get(entity_name, Entity('', '', '')).type}",
            f"描述: {self.entities.get(entity_name, Entity('', '', '')).description}",
            f"\n相关实体 ({len(community_entities)}):",
        ]
        for ent in community_entities:
            summary_parts.append(f"  - {ent}")
        summary_parts.append(f"\n关系 ({len(community_relations)}):")
        for rel in community_relations:
            summary_parts.append(f"  - {rel.source} --[{rel.relation_type}]--> {rel.target}")
        
        return "\n".join(summary_parts)


class GraphRAGEngine:
    """GraphRAG 引擎"""
    
    def __init__(self, llm_client, vector_store):
        self.llm = llm_client
        self.vector_store = vector_store
        self.graph = KnowledgeGraph()
    
    async def build_graph_from_document(self, doc_text: str, source: str):
        """从文档构建知识图谱"""
        # 1. 提取实体
        entities = await self._extract_entities(doc_text, source)
        for ent in entities:
            self.graph.add_entity(ent)
        
        # 2. 抽取关系
        relations = await self._extract_relations(doc_text, entities)
        for rel in relations:
            self.graph.add_relation(rel)
        
        # 3. 生成社区摘要（用于高层级检索）
        for ent in entities:
            summary = self.graph.get_community_summary(ent.name)
            # 将社区摘要存入向量库
            await self.vector_store.insert({
                "content": summary,
                "metadata": {"type": "community_summary", "entity": ent.name},
            })
    
    async def retrieve(self, query: str) -> str:
        """检索：结合向量检索和图谱检索"""
        # 1. 向量检索获取相关 chunk
        vector_results = await self.vector_store.search(query, top_k=5)
        
        # 2. 提取查询中的实体
        query_entities = await self._extract_entities(query, "query")
        
        # 3. 图谱检索：获取相关实体及其社区摘要
        graph_contexts = []
        for ent in query_entities:
            if ent.name in self.graph.entities:
                summary = self.graph.get_community_summary(ent.name)
                graph_contexts.append(summary)
        
        # 4. 综合结果
        contexts = [r["content"] for r in vector_results] + graph_contexts
        return "\n\n".join(contexts)
    
    async def _extract_entities(self, text: str, source: str) -> List[Entity]:
        """使用 LLM 提取实体"""
        prompt = f"从以下文本中提取所有关键实体（人名、技术名词、概念等）：\n{text}"
        response = await self.llm.generate(prompt)
        
        entities = []
        for line in response.split("\n"):
            match = re.match(r"-\s*(\w+)\s*\((\w+)\)\s*:\s*(.+)", line)
            if match:
                entities.append(Entity(
                    name=match.group(1),
                    type=match.group(2),
                    description=match.group(3),
                    source_docs=[source],
                ))
        return entities


# ========== Agentic RAG 实现 ==========

class AgentAction(Enum):
    ROUTE = "route"
    RETRIEVE = "retrieve"
    READ = "read"
    REFLECT = "reflect"
    FINAL_ANSWER = "final_answer"


@dataclass
class AgentState:
    question: str
    context: List[str] = field(default_factory=list)
    reasoning_steps: List[str] = field(default_factory=list)
    step_count: int = 0
    max_steps: int = 10
    done: bool = False
    answer: str = ""


class AgenticRAGAgent:
    """Agentic RAG 代理 — Router/Retriever/Reader 模式"""
    
    def __init__(self, llm_client, retrievers: Dict[str, Any]):
        self.llm = llm_client
        self.retrievers = retrievers
    
    async def run(self, question: str, max_steps: int = 10) -> str:
        """执行 Agentic RAG 推理"""
        state = AgentState(question=question, max_steps=max_steps)
        
        while not state.done and state.step_count < max_steps:
            state.step_count += 1
            action = await self._decide_next_action(state)
            state = await self._execute_action(action, state)
        
        return state.answer
    
    async def _decide_next_action(self, state: AgentState) -> AgentAction:
        """Router：分析当前状态，决定下一步动作"""
        prompt = f"""你是一个 RAG 系统的路由决策器。
当前问题：{state.question}
已检索到的上下文数：{len(state.context)}
推理步骤：{len(state.reasoning_steps)}
当前步数：{state.step_count}/{state.max_steps}

选择下一步动作：
- retrieve: 还需要更多信息
- reflect: 对已有信息进行推理分析
- final_answer: 已有足够信息，可以回答"""
        
        response = await self.llm.generate(prompt)
        
        if "final_answer" in response.lower():
            return AgentAction.FINAL_ANSWER
        elif "reflect" in response.lower():
            return AgentAction.REFLECT
        else:
            return AgentAction.RETRIEVE
    
    async def _execute_action(self, action: AgentAction, 
                               state: AgentState) -> AgentState:
        """执行动作"""
        if action == AgentAction.RETRIEVE:
            # 选择检索器
            prompt = f"为问题选择检索策略：{state.question}"
            strategy = await self.llm.generate(prompt)
            
            # 执行检索
            if "vector" in strategy.lower():
                results = await self.retrievers["vector"].retrieve(state.question)
            elif "graph" in strategy.lower():
                results = await self.retrievers["graph"].retrieve(state.question)
            else:
                results = await self.retrievers["bm25"].retrieve(state.question)
            
            for r in results:
                state.context.append(r.content)
            state.reasoning_steps.append(f"Step {state.step_count}: 检索到 {len(results)} 条结果")
        
        elif action == AgentAction.REFLECT:
            prompt = f"""分析已有信息，找出信息缺口：

问题：{state.question}
已有上下文：
{' '.join(state.context[:3])}

哪些信息还不完整？还需要补充什么？"""
            
            analysis = await self.llm.generate(prompt)
            state.reasoning_steps.append(f"Step {state.step_count}: 分析 - {analysis[:100]}")
        
        elif action == AgentAction.FINAL_ANSWER:
            prompt = f"""基于以下信息回答问题：

问题：{state.question}
上下文：
{' '.join(state.context[:5])}

回答："""
            
            answer = await self.llm.generate(prompt)
            state.answer = answer
            state.done = True
            state.reasoning_steps.append(f"Step {state.step_count}: 生成最终答案")
        
        return state
```

## 错误示例

```python
# 错误 1：GraphRAG 没有关系抽取
def bad_no_relation_extraction():
    """只有实体没有关系 → 不是图，是节点集合"""
    entities = ["FastAPI", "Pydantic", "Starlette"]
    # 没有 "FastAPI uses Pydantic" 这样的关系
    # 无法做多跳推理


# 错误 2：Agentic RAG 没有终止条件
def bad_no_termination():
    """Agent 无限制推理 → 死循环"""
    
    class BadAgent:
        async def run(self, question):
            while True:  # 没有终止条件！
                context = await self.retrieve(question)
                if self.is_satisfied(context):
                    return self.generate(context)
                # 如果没有满意的上下文，永远循环


# 错误 3：GraphRAG 适用于所有场景
def bad_graphrag_everything():
    """小规模简单 Q&A 也用 GraphRAG"""
    # 10 个简单文档，问"FastAPI 是什么"
    # → 传统向量 RAG 即可，GraphRAG 增加复杂性无收益


# 错误 4：Agent 每步都要检索
def bad_always_retrieve():
    """Agent 不做推理，每次都检索"""
    while not done:
        # 每次都检索相同的内容
        # 没有对已有信息的分析和利用
        results = retriever.retrieve(question)
        context.append(results)
```

## 参考来源

- [GraphRAG: 微软开源项目](https://github.com/microsoft/graphrag)
- [Agentic RAG 模式](https://blog.langchain.dev/agentic-rag/)
- [Router/Retriever/Reader 架构](https://arxiv.org/abs/2312.10997)
