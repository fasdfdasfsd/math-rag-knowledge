"""
任务定义模块
-------------
定义 5 个顺序任务，覆盖需求分析到 ECC 变更控制全流程。

关键设计：
  1. 每个 Task 显式指定 name 参数，保证 {{ task_name.output }} 引用确定。
  2. 所有 expected_output 要求输出纯净的 Markdown，禁止对话前缀。
  3. 长文输入任务（架构师、撰写员）包含"先提炼关键点"提示。
  4. ECC 任务末尾输出结构化评分标记，供 main.py 的质量迭代逻辑解析。
  5. 知识库工具和全局记忆工具按需注入，不影响默认流程。
"""
from crewai import Task
from agents import (
    requirement_analyst, system_architect, technical_writer,
    claude_code_reviewer, ecc_controller
)
from tools.knowledge_base import KnowledgeBaseTool
from tools.global_memory import GlobalMemoryTool


def get_tasks(knowledge_dir: str = None, memory_file: str = None):
    """
    构建任务流水线
    :param knowledge_dir: 知识库目录路径，None 则禁用知识库检索
    :param memory_file: 全局记忆文件路径，None 则禁用跨会话记忆
    :return: 有序 Task 列表（长度 = 5）
    """
    # 按需初始化可选工具
    kb_tool = KnowledgeBaseTool(knowledge_dir=knowledge_dir) if knowledge_dir else None
    mem_tool = GlobalMemoryTool(memory_file=memory_file) if memory_file else None

    # ====== 第 1 步：需求分析 ======
    analyze = Task(
        name="analyze_requirements_task",
        description=(
            "主题：{topic}\n"
            "进行需求分析，输出结构化文档（Markdown），包含：\n"
            "1. 引言（目的、范围、定义、参考资料）\n"
            "2. 功能需求列表（含需求编号、描述、优先级）\n"
            "3. 非功能需求（性能、安全、可用性等）\n"
            "4. 用例描述（主要用例，含基本流和备选流）\n"
            "注意：若主题信息不足，请基于行业常识合理推断，并明确标注假设前提。\n"
            "只输出需求分析文档内容本身，不要添加任何解释、问候或对话前缀。"
        ),
        expected_output="仅包含需求分析文档内容的 Markdown",
        agent=requirement_analyst,
        tools=[mem_tool] if mem_tool else None
    )

    # ====== 第 2 步：架构设计（依赖需求分析输出） ======
    architect = Task(
        name="design_architecture_task",
        description=(
            "基于需求文档设计系统架构，包含架构风格、模块划分、接口定义、数据设计等。\n"
            "需求文档内容（可能较长，请先提炼关键功能点和约束条件后再设计）：\n"
            "{{ analyze_requirements_task.output }}\n"
            "输出要求：\n"
            "- 架构风格及选型理由（如分层、微服务、事件驱动等）\n"
            "- 模块划分及职责说明\n"
            "- 核心接口定义（API 端点或模块间接口）\n"
            "- 数据存储方案\n"
            "只输出架构设计部分的 Markdown，不要添加任何解释。"
        ),
        expected_output="仅包含架构设计内容的 Markdown",
        agent=system_architect,
        context=[analyze]
    )

    # ====== 第 3 步：文档撰写（整合需求 + 架构，可选知识库/记忆） ======
    doc_desc = (
        "整合需求文档和架构文档，生成完整的需求规格说明书（SRS）。\n"
        "严格遵循 IEEE 830-1998 标准结构，必须包含以下所有章节：\n"
        "1. 封面（项目名称、版本号 v1.0.0、日期、编制单位）\n"
        "2. 版本记录\n"
        "3. 引言（目的、文档约定、预期读者、产品范围、参考文献）\n"
        "4. 综合描述（产品前景、功能概述、用户特征、运行环境、限制、假设依赖）\n"
        "5. 外部接口需求（用户界面、硬件接口、软件接口、通信接口）\n"
        "6. 系统特性（功能需求详情 + 用例描述）\n"
        "7. 非功能需求（性能、安全、质量属性）\n"
        "8. 验收标准\n"
        "9. 附录（词汇表引用、待确定问题列表）\n\n"
        "需求文档：{{ analyze_requirements_task.output }}\n"
        "架构文档：{{ design_architecture_task.output }}\n"
        "处理策略：先分别提取两份输入文档的核心信息，再按照 IEEE 830 模板重组，"
        "避免原文照搬导致长度爆炸。\n"
        "输出必须是一个完整的、可独立交付的 Markdown 文档，不要包含任何额外解释或评论。"
    )
    doc_tools = []
    if kb_tool:
        doc_tools.append(kb_tool)
        doc_desc += " 你可以使用知识库工具 'knowledge_base' 检索企业模板或术语表。"
    if mem_tool:
        doc_tools.append(mem_tool)
    write = Task(
        name="write_document_task",
        description=doc_desc,
        expected_output="完整的 IEEE 830 需求规格说明书（Markdown）",
        agent=technical_writer,
        context=[analyze, architect],
        tools=doc_tools if doc_tools else None
    )

    # ====== 第 4 步：代码级审查 ======
    review = Task(
        name="review_code_task",
        description=(
            "对文档进行代码级审查，检查以下方面：\n"
            "- 接口定义的完整性和正确性\n"
            "- 伪代码或技术方案可行性\n"
            "- 边界条件和异常处理\n"
            "- 潜在的安全漏洞\n\n"
            "文档内容：{{ write_document_task.output }}\n"
            "若文档过长，集中检查架构、接口和数据流等关键章节。\n"
            "直接在原文档基础上修改，输出修订后的完整文档，不要附加审查意见或对话。"
        ),
        expected_output="修订后的完整需求规格说明书（Markdown）",
        agent=claude_code_reviewer,
        context=[write]
    )

    # ====== 第 5 步：ECC 变更控制 + 质量评分 ======
    ecc = Task(
        name="ecc_check_task",
        description=(
            "进行变更控制和一致性检查，确保需求与架构无矛盾，补充版本信息。\n"
            "文档内容：{{ review_code_task.output }}\n\n"
            "检查项包括：\n"
            "- 需求可追溯性（每个功能需求是否有对应的架构支持）\n"
            "- 内部一致性（术语是否统一、描述是否自洽）\n"
            "- 模块耦合度（接口是否合理、依赖是否清晰）\n"
            "- 未解决的待定项（是否有 TODO 或待确定标记未处理）\n"
            "- 版本信息完整性\n\n"
            "**重要：请在最终文档末尾（所有文档正文内容之后）添加以下标记：**\n"
            "### ECC_QUALITY_SCORE: X/10\n"
            "（X 为 1-10 的整数，10 代表完美无缺）\n"
            "若评分低于 8，请在下一行用分号分隔列出主要问题：\n"
            "### ECC_ISSUES: 问题1; 问题2; 问题3\n"
            "注意：质量标记和问题行不属于文档正文，是供系统使用的元数据。\n"
            "输出最终版完整文档，不添加任何解释性前缀。"
        ),
        expected_output="最终通过 ECC 验证的完整文档（末尾带评分标记）",
        agent=ecc_controller,
        context=[review]
    )

    return [analyze, architect, write, review, ecc]