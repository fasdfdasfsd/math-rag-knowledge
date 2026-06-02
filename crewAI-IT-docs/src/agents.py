"""
智能体定义模块
----------------
本模块创建 5 个专职智能体，通过 llm_config.create_llm_for_role()
按角色名获取 LLM 实例，实现模型与角色的解耦。

角色-模型映射当前配置：
  - 需求分析师 → DeepSeek V3（温度 0.4，鼓励发散）
  - 系统架构师 → DeepSeek V4 Pro Max（最强推理）
  - 技术文档撰写员 → DeepSeek V3（温度 0.2，保证严谨）
  - 代码审查员 → DeepSeek V4 Pro（温度 0.1，严谨审查）
  - ECC 变更控制员 → DeepSeek V3（温度 0.1，严格校验）

所有智能体均禁止委托（allow_delegation=False），确保流水线顺序执行。
"""
from crewai import Agent
from utils.llm_config import create_llm_for_role

# ============================================================
# 需求分析师 — 使用稍高温度，利于捕捉边缘用例和推断假设
# ============================================================
requirement_analyst = Agent(
    role="需求分析师",
    goal="从用户简短主题中提取、分析并结构化软件需求，输出功能需求列表和用例。",
    backstory=(
        "经验丰富的业务分析师，擅长将模糊想法转化为可测试、可追溯的需求。"
        "能基于常识合理推断缺失信息，并标注假设前提。"
    ),
    llm=create_llm_for_role("analyst"),
    verbose=True,
    allow_delegation=False
)

# ============================================================
# 系统架构师 — 使用 V4 Pro Max 模式，获取最强推理能力
# ============================================================
system_architect = Agent(
    role="系统架构师",
    goal="基于需求设计系统架构：模块划分、技术选型、接口定义。",
    backstory=(
        "资深架构师，精通微服务、分层架构、事件驱动等多种架构风格，"
        "能输出可落地的架构方案，包含技术选型理由和接口设计要点。"
    ),
    llm=create_llm_for_role("architect"),
    verbose=True,
    allow_delegation=False
)

# ============================================================
# 技术文档撰写员 — 使用 V3，负责长文本整合与模板遵循
# ============================================================
technical_writer = Agent(
    role="技术文档撰写员",
    goal="整合需求与架构，生成标准的软件需求规格说明书（Markdown）。",
    backstory=(
        "严谨的技术文档工程师，严格遵循 IEEE 830-1998 标准，"
        "能处理长文本输入，提取核心信息并按标准模板重组为完整文档。"
    ),
    llm=create_llm_for_role("writer"),
    verbose=True,
    allow_delegation=False
)

# ============================================================
# 代码审查员 — 使用 V4 Pro，深度审查技术方案与伪代码
# ============================================================
claude_code_reviewer = Agent(
    role="代码审查员",
    goal="审查文档中的技术方案、接口定义、伪代码，发现缺陷并提出改进。",
    backstory=(
        "由 DeepSeek V4 Pro 驱动的代码审查专家，"
        "关注边界条件、安全漏洞、错误处理和技术方案的可行性，"
        "能直接在文档基础上进行修订而不改变原有结构。"
    ),
    llm=create_llm_for_role("reviewer"),
    verbose=True,
    allow_delegation=False
)

# ============================================================
# ECC 工程变更控制员 — 使用 V3，严格一致性校验
# ============================================================
ecc_controller = Agent(
    role="ECC 工程变更控制员",
    goal="检查需求一致性、版本记录，确保文档无矛盾，并输出质量评分。",
    backstory=(
        "工程变更控制专家，擅长发现需求冲突、术语不一致和缺失依赖，"
        "能给出可量化的质量评估（1-10 分），并列出具体问题清单。"
    ),
    llm=create_llm_for_role("ecc"),
    verbose=True,
    allow_delegation=False
)