"""
大语言模型配置模块
-------------------
提供基于角色名称的 LLM 实例工厂，实现模型与角色的解耦。
通过 ROLE_MODEL_MAP 可灵活切换/升级模型，无需修改 Agent 代码。

当前配置：
  - analyst (需求分析师)   → DeepSeek V3（温度 0.4）
  - architect (系统架构师) → DeepSeek V4 Pro（Max 推理模式）
  - writer (文档撰写员)     → DeepSeek V3（温度 0.2）
  - reviewer (代码审查员)  → DeepSeek V4 Pro（温度 0.1）
  - ecc (变更控制员)       → DeepSeek V3（温度 0.1）
"""
import os
from typing import Any

from crewai import LLM

# ============================================================
# 角色-模型配置映射表
# 修改此处即可全局切换模型，无需改动 agents.py
# ============================================================
ROLE_MODEL_MAP: dict[str, dict[str, Any]] = {
    "analyst": {
        "model": "deepseek/deepseek-chat",
        "temperature": 0.4,         # 略高温度，鼓励发散思维和假设推断
        "max_tokens": 300000,
        "api_key_env": "DEEPSEEK_API_KEY",
        "base_url_env": "DEEPSEEK_BASE_URL",
    },
    "architect": {
        "model": "deepseek/deepseek-v4-pro",
        "temperature": 0.2,
        "max_tokens": 300000,         # 大输出空间，确保架构设计详尽
        "extra_body": {"reasoning_effort": "max"},  # V4 Pro Max 推理
        "api_key_env": "DEEPSEEK_API_KEY",
        "base_url_env": "DEEPSEEK_BASE_URL",
    },
    "writer": {
        "model": "deepseek/deepseek-chat",
        "temperature": 0.2,
        "max_tokens": 300000,
        "api_key_env": "DEEPSEEK_API_KEY",
        "base_url_env": "DEEPSEEK_BASE_URL",
    },
    "reviewer": {
        "model": "deepseek/deepseek-v4-pro",
        "temperature": 0.1,         # 极低温度，保证审查严格一致
        "max_tokens": 300000,
        "extra_body": {"reasoning_effort": "medium"},  # 平衡速度与深度
        "api_key_env": "DEEPSEEK_API_KEY",
        "base_url_env": "DEEPSEEK_BASE_URL",
    },
    "ecc": {
        "model": "deepseek/deepseek-chat",
        "temperature": 0.1,
        "max_tokens": 300000,
        "api_key_env": "DEEPSEEK_API_KEY",
        "base_url_env": "DEEPSEEK_BASE_URL",
    },
}


def create_llm_for_role(role: str) -> LLM:
    """
    根据角色名创建对应的 LLM 实例。
    :param role: 角色键，如 'analyst'、'architect'、'writer'、'reviewer'、'ecc'
    :return: 配置好的 LLM 对象
    :raises ValueError: 当角色未在 ROLE_MODEL_MAP 中定义或 API Key 未设置时
    """
    config = ROLE_MODEL_MAP.get(role)
    if not config:
        raise ValueError(
            f"未定义的角色：'{role}'，请在 ROLE_MODEL_MAP 中添加配置"
        )

    api_key = os.getenv(config["api_key_env"])
    base_url = os.getenv(
        config.get("base_url_env", "DEEPSEEK_BASE_URL"),
        "https://api.deepseek.com/v1"
    )
    if not api_key:
        raise ValueError(
            f"环境变量 {config['api_key_env']} 未设置，请检查 .env 文件"
        )

    extra = config.get("extra_body", {"reasoning_effort": None})

    return LLM(
        model=config["model"],
        api_key=api_key,
        base_url=base_url,
        temperature=config["temperature"],
        max_tokens=config["max_tokens"],
        extra_body=extra,
    )


def get_deepseek_llm(temperature: float = 0.2, max_tokens: int = 1000000) -> LLM:
    """
    兼容旧接口：创建默认的 DeepSeek LLM 实例。
    推荐新代码使用 create_llm_for_role()。
    """
    return create_llm_for_role("analyst")
