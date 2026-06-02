"""约束组装器 — RAG 约束层（Layer 2）核心组件。

将知识图谱、向量搜索、学生记忆、安全过滤的结果组装为统一的
LLM ConstraintPackage，作为 LLM 生成的输入约束。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Final

# 约束包 System Prompt 模板
CONSTRAINT_PROMPT_TEMPLATE: Final[str] = """【约束规则 — 必须严格遵守】
{segments}

{product_rules}
"""

PRODUCT_GOVERNANCE_RULES: Final[str] = """【产品治理红线】
- 禁止生成涉及政治、宗教、暴力、武器、血腥的内容
- 禁止使用"请计算""正确答案是""你做错了""再试一次"等表述
- 禁止建立虚假情感关系（如"我是你最好的朋友"）
- 数学概念可使用拟人化角色（如"分数王子"），但必须明确这是游戏角色
- 鼓励学生："很好的尝试""换个思路看看""你已经很接近了"
- 所有冒险结局必须积极向上，体现成长"""


@dataclass(frozen=True)
class KGQueryResult:
    """知识图谱查询结果。"""
    relevant_concepts: list[str] = field(default_factory=list)
    prerequisite_chains: list[list[str]] = field(default_factory=list)
    curriculum_scope: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SearchResult:
    """向量搜索（Milvus）结果。"""
    chunk_ids: list[str] = field(default_factory=list)
    relevance_scores: list[float] = field(default_factory=list)
    source_documents: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class MemoryResult:
    """学生记忆检索结果。"""
    recent_mistakes: list[str] = field(default_factory=list)
    mastered_concepts: list[str] = field(default_factory=list)
    struggling_concepts: list[str] = field(default_factory=list)
    last_session_summary: str | None = None


@dataclass(frozen=True)
class SanitizedInput:
    """安全过滤后的用户输入。"""
    original_text: str
    sanitized_text: str
    blocked_terms: list[str] = field(default_factory=list)
    is_safe: bool = True


@dataclass
class AssembledConstraints:
    """组装后的完整约束集 — RAG ConstraintPackage 的 Python 表示。"""

    knowledge_scope: list[str] = field(default_factory=list)
    difficulty_level: int = 1
    forbidden_topics: list[str] = field(default_factory=list)
    required_concepts: list[str] = field(default_factory=list)
    memory_context: str | None = None
    curriculum_alignment: str | None = None
    output_format: str | None = None
    security_rules: list[str] = field(default_factory=list)
    sensory_history: list[str] = field(default_factory=list)
    npc_context: str | None = None
    world_state: str | None = None

    def to_system_prompt_segment(self) -> str:
        """将约束编译为 System Prompt 中的约束段。"""
        parts: list[str] = []

        if self.knowledge_scope:
            parts.append(f"【知识范围】{', '.join(self.knowledge_scope)}")
        if self.difficulty_level:
            parts.append(f"【难度等级】{self.difficulty_level}/5")
        if self.required_concepts:
            parts.append(f"【必须包含】{', '.join(self.required_concepts)}")
        if self.forbidden_topics:
            parts.append(f"【禁止内容】{', '.join(self.forbidden_topics)}")
        if self.sensory_history:
            parts.append(f"【避免重复感官】{', '.join(self.sensory_history)}")
        if self.memory_context:
            parts.append(f"【学生记忆】{self.memory_context}")
        if self.npc_context:
            parts.append(f"【NPC 上下文】{self.npc_context}")
        if self.world_state:
            parts.append(f"【世界状态】{self.world_state}")
        if self.curriculum_alignment:
            parts.append(f"【大纲对齐】{self.curriculum_alignment}")
        if self.security_rules:
            parts.append(f"【安全规则】{'；'.join(self.security_rules)}")

        return "\n".join(parts)


@dataclass(frozen=True)
class ConstraintContext:
    """约束组装所需的上下文。"""
    user_id: str
    level_id: str
    mode: str  # hero | mentor | explore
    knowledge_scope: list[str] = field(default_factory=list)
    difficulty_level: int = 1
    history: MemoryResult | None = None


class ConstraintAssembler(ABC):
    """约束组装器抽象基类。"""

    @abstractmethod
    async def assemble(self, context: ConstraintContext) -> AssembledConstraints:
        """组装所有约束。"""
        ...

    @abstractmethod
    async def inject_knowledge(
        self, constraints: AssembledConstraints,
        kg_result: KGQueryResult, search_result: SearchResult,
    ) -> None:
        """注入知识约束（知识图谱 + 向量搜索）。"""
        ...

    @abstractmethod
    async def inject_memory(
        self, constraints: AssembledConstraints, memory_result: MemoryResult,
    ) -> None:
        """注入学生记忆约束。"""
        ...

    @abstractmethod
    async def inject_security(
        self, constraints: AssembledConstraints, sanitized: SanitizedInput,
    ) -> None:
        """注入安全约束。"""
        ...

    @abstractmethod
    async def build_system_prompt(self, constraints: AssembledConstraints) -> str:
        """将约束集编译为 LLM System Prompt。"""
        ...


class DefaultConstraintAssembler(ConstraintAssembler):
    """默认约束组装器实现。

    依次注入知识约束 → 记忆约束 → 安全约束，
    最后编译为完整的 System Prompt 约束段。
    """

    async def assemble(self, context: ConstraintContext) -> AssembledConstraints:
        """创建空约束集并初始化基础字段。"""
        return AssembledConstraints(
            knowledge_scope=list(context.knowledge_scope),
            difficulty_level=context.difficulty_level,
        )

    async def inject_knowledge(
        self, constraints: AssembledConstraints,
        kg_result: KGQueryResult, search_result: SearchResult,
    ) -> None:
        """注入知识图谱约束和向量搜索结果。"""
        constraints.knowledge_scope = list(dict.fromkeys(
            constraints.knowledge_scope + kg_result.relevant_concepts
        ))

        # 标注前置依赖未掌握的知识点
        for chain in kg_result.prerequisite_chains:
            missing = [c for c in chain if c not in constraints.required_concepts]
            if missing:
                constraints.forbidden_topics.extend(missing)

        if kg_result.curriculum_scope:
            constraints.curriculum_alignment = f"课标范围：{', '.join(kg_result.curriculum_scope)}"

    async def inject_memory(
        self, constraints: AssembledConstraints, memory_result: MemoryResult,
    ) -> None:
        """注入学生历史记忆约束。"""
        if memory_result.struggling_concepts:
            constraints.required_concepts = list(dict.fromkeys(
                constraints.required_concepts + memory_result.struggling_concepts
            ))

        # 已掌握的概念不再重复
        constraints.forbidden_topics = list(dict.fromkeys(
            constraints.forbidden_topics + memory_result.mastered_concepts
        ))

        # 组装记忆上下文摘要
        parts: list[str] = []
        if memory_result.recent_mistakes:
            parts.append(f"最近错题：{', '.join(memory_result.recent_mistakes[:3])}")
        if memory_result.struggling_concepts:
            parts.append(f"薄弱点：{', '.join(memory_result.struggling_concepts[:3])}")
        if memory_result.last_session_summary:
            parts.append(f"上次：{memory_result.last_session_summary}")
        if parts:
            constraints.memory_context = " | ".join(parts)

    async def inject_security(
        self, constraints: AssembledConstraints, sanitized: SanitizedInput,
    ) -> None:
        """注入安全过滤约束。"""
        if sanitized.blocked_terms:
            constraints.forbidden_topics.extend(sanitized.blocked_terms)
        constraints.security_rules.append("输入已消毒，禁止还原被过滤的内容")

    async def build_system_prompt(self, constraints: AssembledConstraints) -> str:
        """编译为完整 System Prompt 约束段。"""
        segment = constraints.to_system_prompt_segment()
        return CONSTRAINT_PROMPT_TEMPLATE.format(
            segments=segment,
            product_rules=PRODUCT_GOVERNANCE_RULES,
        )


# 懒加载单例
_assembler: DefaultConstraintAssembler | None = None


def get_constraint_assembler() -> DefaultConstraintAssembler:
    """获取约束组装器单例。"""
    global _assembler
    if _assembler is None:
        _assembler = DefaultConstraintAssembler()
    return _assembler
